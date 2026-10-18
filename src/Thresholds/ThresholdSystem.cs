using System;
using System.Collections.Generic;
using Backrooms.Map;
using Backrooms.Worldgen;
using ProtoBuf;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// The Backrooms' topology lies. The levels are laid out as rings, and you can walk outward through them all; but
/// the rings are only how the world is built. The game is the network of ways between them:
/// <list type="bullet">
/// <item>Elevators (Levels 3, 4 and 5) each lead to one fixed place, beside another elevator in Level 3, 4 or 5 (from
/// the hotel, now and then Level 1, with a thin spot back), and that elevator brings you back.</item>
/// <item>A few of the hotel's locked doors open after all, onto somewhere far away.</item>
/// <item>Falling into one of Level 0's pits drops you into Level 2.</item>
/// <item>Stairwells: Level 1's come out of other stairwells, or now and then in the Abandoned Office; Level 4's
/// come out of other stairwells on the same floor, or now and then back in Level 0; the hotel's staff stairs come
/// out in the dark of Level 6.</item>
/// <item>A few of Level 4's vending machines and the wires strung across Level 6's passages drop you into
/// Level 6.1, the Snackrooms. Its rusty doors lead back into Level 6, its glass doors to the offices or the hotel,
/// its vents to the Electrical Station, and its kitchen doors into another food court.</item>
/// <item>Level 6's stairs down, found by the sound of waves, come out in an entry room in the ceiling of Level 7,
/// and you fall through into the sea. From layout version 9 they are a stairwell walked down to its landing, and come
/// out at the foot of the stairs that come down into an entry room hung from the high ceiling, a doorway across it onto
/// the sea and a rope ladder down; back up those stairs is back to that landing.</item>
/// <item>In Level 7, swim down into the circle of stones to reach Level 9, or into a cave mouth in the midnight
/// zone to reach the 9th Road in Level 8. Level 8's vents lead up into Level 2.</item>
/// <item>A gate at the end of a field behind the houses of Level 9 opens onto Level 10, and diving to the bottom
/// of one of Level 10's lakes brings you up in Level 7.</item>
/// <item>Level 11, the Endless City, is no ring: you noclip into it, through a stretch of barn wall in Level 10
/// that isn't quite there. It is the hub of the Backrooms. An office tower's elevators go to Level 4 and a hotel's
/// to Level 5; an apartment block's basement door to Level 0, a garage's ramp to Level 1, an open manhole or a
/// subway maintenance door to Level 2, a substation's door to Level 3; a dark doorway off an alley to Level 6, the
/// deep middle of a park fountain to Level 7, a fallen-in street to Level 8, a rowhouse's front door to Level 9, a
/// patch of wheat in a park to Level 10, and a diner's kitchen door to the Snackrooms.</item>
/// </list>
/// Where each one leads, which are two-way and how the way back is made is all in <see cref="ThresholdNetwork"/>;
/// this system notices players going through thresholds, moves them, and keeps the network saved with the world.
/// </summary>
public partial class ThresholdSystem : ModSystem
{
    private const string SaveKey = "backrooms-thresholds";
    private const string Channel = "backrooms-thresholds";
    private const int CooldownMs = 4000;

    /// <summary>
    /// Player attribute: until when (world milliseconds) a fall cannot kill them. It is set while they drop through a
    /// pit, an open manhole, a fallen-in street or a hatch, and lasts a while after, so a fall that hurts on the far
    /// side, or one that no threshold caught (a pit that leads nowhere, a destination not found), leaves them hurt
    /// but alive with at least <see cref="FallGraceHealth"/> health.
    /// </summary>
    private const string FallGraceKey = "backrooms:fallGraceUntil";
    private const int FallGraceMs = 10000;
    private const float FallGraceHealth = 1f;
    private const int ElevatorRideMs = 1500;

    /// <summary>
    /// Server to client: turn to face this way (someone put down on a flight of stairs faces down it, and someone put
    /// down on the landing of a stairwell's flight faces away from it).
    /// </summary>
    [ProtoContract]
    public class FacePacket
    {
        [ProtoMember(1)] public float Yaw;
    }

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private ThresholdNetwork network;
    private int thinSpotId;
    private readonly Dictionary<string, long> busyUntilMs = new();
    // The pit tile each player was last seen near, and the drop it belongs to, whose arrival is already loading
    private readonly Dictionary<string, (int X, int Z, (int X, int Z) Source)> preloadedPit = new();
    // Whether each player stood in a thin spot at the last tick: stepping into one takes you back, standing in the
    // one you arrived in does not
    private readonly Dictionary<string, bool> inThinSpot = new();
    // Who was put down on a flight of stairs and has not stepped off it since: the stairs they stand on take nobody
    // anywhere until they have (or they would climb straight back the way they came)
    private readonly HashSet<string> offStairsFirst = new();

    // Per-player cache of the cell they are standing in, so the tick does not rebuild it every time
    private readonly Dictionary<string, (int Mx, int Mz, Tile[] Tiles)> cellCache = new();
    // Where each player was at the last tick, to notice them walking through a gate into another level
    private readonly Dictionary<string, (int Level, double X, double Z)> lastSpot = new();

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockBehaviorClass("BackroomsThreshold", typeof(BlockBehaviorThreshold));
        api.Network.RegisterChannel(Channel).RegisterMessageType<FacePacket>().RegisterMessageType<TransitionPacket>();
    }

    public override void StartClientSide(ICoreClientAPI api)
    {
        StartTransitionClient(api);
        api.Network.GetChannel(Channel).SetMessageHandler<FacePacket>(packet =>
        {
            // The camera decides which way the player looks; the entity follows it
            if (api.World.Player?.Entity is not { } self) return;
            api.World.Player.CameraYaw = packet.Yaw;
            self.Pos.Yaw = packet.Yaw;
            self.BodyYaw = packet.Yaw;
        });
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () => RegisterWayBackCommand(api));
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            network = new ThresholdNetwork(layout, geometry, api.WorldManager.Seed);
            byte[] saved = api.WorldManager.SaveGame.GetData(SaveKey);
            if (!network.Load(saved))
            {
                // Keep what could not be read rather than lose it when the links are next saved (and keep the first
                // such copy, should it happen again)
                if (api.WorldManager.SaveGame.GetData(SaveKey + "-unreadable") == null)
                    api.WorldManager.SaveGame.StoreData(SaveKey + "-unreadable", saved);
                api.Logger.Error("[backrooms] The saved threshold links could not all be read (kept as {0}-unreadable); {1} were, the rest will find their places again",
                    SaveKey, network.Count);
            }
            LoadWayBacks(api);
            thinSpotId = api.World.GetBlock(new AssetLocation("backrooms:thinspot"))?.BlockId ?? 0;
            api.Event.GameWorldSave += () =>
            {
                if (!network.Dirty) return;
                // (The ways back built at arrivals go beside the links, under a key of their own: the links' layout is unchanged)
                api.WorldManager.SaveGame.StoreData(WayBackSaveKey, network.SaveWayBacks());
                api.WorldManager.SaveGame.StoreData(SaveKey, network.Save());
            };
            api.Event.RegisterGameTickListener(OnTick, 200);
            api.Event.PlayerNowPlaying += SoftenFalls;
            api.Event.PlayerDisconnect += player =>
            {
                busyUntilMs.Remove(player.PlayerUID);
                cellCache.Remove(player.PlayerUID);
                preloadedPit.Remove(player.PlayerUID);
                inThinSpot.Remove(player.PlayerUID);
                offStairsFirst.Remove(player.PlayerUID);
                lastSpot.Remove(player.PlayerUID);
            };
        });
    }

    /// <summary>The level at a block position.</summary>
    public int LevelAt(BlockPos pos) => layout?.LevelAt(WorldLayout.MacroOf(pos.X), WorldLayout.MacroOf(pos.Z)) ?? -1;

    /// <summary>Whether using the threshold block at a position would take someone somewhere (rather than being locked, out of order or nowhere).</summary>
    public bool LeadsSomewhere(BlockPos pos, string kind) => network != null && network.Used(pos.X, pos.Z, kind, out _) != null;

    // ================= Thresholds you use =================

    /// <summary>Called when a player uses a threshold block (an elevator, a door, a vent, a thin spot).</summary>
    public void Use(IServerPlayer player, BlockPos pos, string kind)
    {
        if (network == null || IsBusy(player) || !CanTravel(player)) return;
        // The throne room's doors are no part of the network: only one opens, and a different one each day
        if (kind == "thronedoor")
        {
            busyUntilMs[player.PlayerUID] = sapi.World.ElapsedMilliseconds + 1500;
            sapi.ModLoader.GetModSystem<Regions.MotionSystem>()?.UseThroneDoor(player, pos);
            return;
        }
        // Level !'s doors that lead nowhere (the stuck hall door, the chained door, side doors, false exits)
        if (RunUse(player, pos, kind)) return;
        Passage passage = network.Used(pos.X, pos.Z, kind, out string refusal);
        if (passage == null)
        {
            Play(pos, "game:sounds/effect/latch");
            string message = refusal switch
            {
                "outoforder" => "backrooms:elevator-outoforder",
                "nowhere" => "backrooms:thinspot-nowhere",
                "endexit" => "backrooms:endexit-locked",
                "endfake" => "backrooms:endfake-shut",
                "l3999-staff" => "backrooms:l3999-staff-locked",
                _ => "backrooms:door-locked",
            };
            player.SendIngameError("backrooms-" + refusal, Lang.Get(message));
            busyUntilMs[player.PlayerUID] = sapi.World.ElapsedMilliseconds + 500;
            return;
        }

        // Whoever comes back this way is put down where this player is standing now
        EntityPos from = player.Entity.Pos;
        Link? destination = network.Take(passage, new Link(from.X, from.Y + 0.05, from.Z, false));
        if (destination == null)
        {
            Play(pos, "game:sounds/effect/latch");
            player.SendIngameError("backrooms-nowhere", Lang.Get("backrooms:thinspot-nowhere"));
            busyUntilMs[player.PlayerUID] = sapi.World.ElapsedMilliseconds + 2000;
            return;
        }
        if (passage.Sound != null) Play(pos, passage.Sound);
        if (kind != "elevator")
        {
            Go(player, passage, destination, kind is "thinspot" or "vent" or "endvent" ? "plain" : "door");
            return;
        }

        // Start loading where it goes while the car rides, and take everyone standing in it along
        Link arrival = destination.Value;
        Preload(arrival);
        List<IServerPlayer> riders = PlayersNear(player, 2.5);
        var boarded = new Dictionary<string, Vec3d>();
        foreach (IServerPlayer rider in riders)
        {
            busyUntilMs[rider.PlayerUID] = sapi.World.ElapsedMilliseconds + ElevatorRideMs + CooldownMs;
            SendTransition(rider, TransitionPhase.Begin, "elevator");
            boarded[rider.PlayerUID] = rider.Entity.Pos.XYZ;
        }
        sapi.Event.RegisterCallback(_ =>
        {
            foreach (IServerPlayer rider in riders)
            {
                // Anyone who stepped out of the car before the doors closed stays behind
                if (!CanTravel(rider) || rider.Entity.Pos.SquareDistanceTo(boarded[rider.PlayerUID]) > 2.5 * 2.5)
                {
                    busyUntilMs.Remove(rider.PlayerUID);
                    SendTransition(rider, TransitionPhase.End, "elevator");
                    continue;
                }
                Link to = Redirect(rider, passage, arrival);
                bool redirected = !to.Equals(arrival);
                Remember(rider, boarded[rider.PlayerUID], arrival, passage.TwoWay, arrived: !redirected);
                Arrive(rider, redirected ? to with { Marker = false } : to, "elevator", redirected ? null : passage.Source);
            }
            sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/metaldoor"), arrival.X, arrival.Y, arrival.Z, null, randomizePitch: true, range: 16);
        }, ElevatorRideMs);
    }

    /// <summary>Carries whoever has just won the King's trial out of the throne room, where his table sends them.</summary>
    public void CarryFromTrial(IServerPlayer player)
    {
        if (network == null || !CanTravel(player)) return;
        // The second chair, at the foot of the King's table
        (int X, int Z) chair = (layout.MotionOriginX - WorldLayout.CastleSize / 2 + 27, layout.MotionOriginZ - WorldLayout.CastleSize / 2 + 31);
        Passage passage = network.Trial(chair);
        Go(player, passage, network.Take(passage, null));
    }

    /// <summary>
    /// Called when a player presses the buttons of a vending machine. A few of Level 4's machines take whoever does
    /// to the Snackrooms, every time; returns whether this is one of them (it never serves anyone, either way).
    /// </summary>
    public bool UseVendingMachine(IServerPlayer player, BlockPos pos)
    {
        if (network == null) return false;
        Passage passage = network.Vending(pos.X, pos.Z);
        if (passage == null) return false;
        if (IsBusy(player) || !CanTravel(player)) return true;
        Link? destination = network.Take(passage, null);
        if (destination == null) return true;
        Play(pos, passage.Sound);
        Go(player, passage, destination, "door");
        return true;
    }

    // ================= Thresholds you stumble through =================

    private void OnTick(float dt)
    {
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer player || !CanTravel(player) || player.Entity.Teleporting) continue;
            if (player.WorldData.CurrentGameMode == EnumGameMode.Spectator) continue;

            EntityPos pos = player.Entity.Pos;
            int x = (int)Math.Floor(pos.X), z = (int)Math.Floor(pos.Z);

            // Stepping into a thin spot takes you back the way it came (standing in the one you arrived in does not, nor
            // one you were standing in when you joined)
            bool thin = thinSpotId != 0 && (ThinSpotAt(x, (int)Math.Floor(pos.Y), z) || ThinSpotAt(x, (int)Math.Floor(pos.Y + 1), z));
            bool wasThin = inThinSpot.TryGetValue(player.PlayerUID, out bool was) ? was : thin;
            inThinSpot[player.PlayerUID] = thin;
            bool busy = IsBusy(player);
            if (thin && !wasThin && !busy)
            {
                Use(player, new BlockPos(x, (int)Math.Floor(pos.Y), z), "thinspot");
                continue;
            }

            int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
            int level = layout.LevelAt(mx, mz);
            if (!busy) NoticeGate(player, level, pos);
            if (level is 2 or 3 or 8) continue;

            Tile tile = CellOf(player, mx, mz)[WorldLayout.TileIndex(x - mx * WorldLayout.MacroSize, z - mz * WorldLayout.MacroSize)];
            double rel = pos.Y - geometry.FloorFor(level);

            // Dropping into a hole in the floor: whatever comes of it, the fall will not kill (see FallGraceKey). And a
            // drop is never held up by the cooldown after a trip, which is there so nobody bounces straight back through
            // the threshold they arrived beside: nobody arrives in a hole, and a fall does not wait
            bool dropping = rel < -0.5 && IsDrop(tile);
            if (dropping) player.Entity.Attributes.SetLong(FallGraceKey, sapi.World.ElapsedMilliseconds + FallGraceMs);
            // Put down on a flight of stairs: they must step off it before any flight takes them anywhere again, so
            // they can walk down and come back up later, but do not go straight back up the way they came
            bool stepOff = offStairsFirst.Contains(player.PlayerUID);
            if (stepOff && tile.Stair == 0)
            {
                offStairsFirst.Remove(player.PlayerUID);
                stepOff = false;
            }
            if (busy && !dropping || stepOff) continue;

            if (level is 0 or 11) PreloadNearbyDrop(player, x, z, rel);

            Passage passage = network.Walked(x, z, tile, rel);
            if (passage == null) continue;
            // Level 94's rusted gates open only at twilight; at any other hour they are only a gate
            if (passage.Twilight && !Regions.MotionSystem.IsTwilight(sapi.World.Calendar)) continue;
            // The far places (ids 14-20) may hold theirs shut
            if (!(RunMayPass(player, passage) && FunMayPass(player, passage) && EndMayPass(player, passage) && HubMayPass(player, passage)
                && L974MayPass(player, passage) && L3999MayPass(player, passage) && L188MayPass(player, passage))) continue;
            Go(player, passage, network.Take(passage, passage.TwoWay ? network.HomeFor(passage) : null), dropping ? "fall" : "walk");
        }
    }

    /// <summary>A hole in the floor that a person falls down (a dry one: those into water need no softening).</summary>
    private static bool IsDrop(in Tile tile) => tile.Kind == TileKind.Pit || tile.Under is Unders.L188Hatch or Unders.PitBottom;

    /// <summary>A fall while <see cref="FallGraceKey"/> lasts hurts as usual but leaves at least <see cref="FallGraceHealth"/>.</summary>
    private void SoftenFalls(IServerPlayer player)
    {
        if (player.Entity?.GetBehavior<Vintagestory.GameContent.EntityBehaviorHealth>() is not { } health) return;
        health.onDamaged += (damage, source) =>
        {
            if (source.Source != EnumDamageSource.Fall || player.Entity == null) return damage;
            if (player.Entity.Attributes.GetLong(FallGraceKey, 0) <= sapi.World.ElapsedMilliseconds) return damage;
            return Math.Min(damage, Math.Max(0f, health.Health - FallGraceHealth));
        };
    }

    /// <summary>
    /// Near the edge of a pit, an open manhole or a fallen-in street, start loading the place it drops into, so the
    /// fall never outlasts the trip.
    /// </summary>
    private void PreloadNearbyDrop(IServerPlayer player, int x, int z, double rel)
    {
        if (rel < -1) return;
        bool known = preloadedPit.TryGetValue(player.PlayerUID, out var last);
        for (int dz = -2; dz <= 2; dz++)
            for (int dx = -2; dx <= 2; dx++)
            {
                int px = x + dx, pz = z + dz;
                Tile near = layout.TileAt(px, pz);
                if (near.Kind != TileKind.Pit) continue;
                // Still beside the same edge as at the last tick: that drop is loading already (this saves finding the
                // whole of the pit five times a second)
                if (known && last.X == px && last.Z == pz) return;
                Passage drop = network.Walked(px, pz, near, -100);
                if (drop == null) continue; // a pit that leads nowhere: look on for one that does
                preloadedPit[player.PlayerUID] = (px, pz, drop.Source);
                if (known && last.Source == drop.Source) return;
                if (network.Take(drop, null) is { } below) Preload(below);
                return;
            }
    }

    // (Reused by the tick: it only ever runs on the main thread)
    private readonly BlockPos probe = new(0);

    private bool ThinSpotAt(int x, int y, int z) => sapi.World.BlockAccessor.GetBlock(probe.Set(x, y, z)).BlockId == thinSpotId;

    private Tile[] CellOf(IServerPlayer player, int mx, int mz)
    {
        if (cellCache.TryGetValue(player.PlayerUID, out var cached) && cached.Mx == mx && cached.Mz == mz) return cached.Tiles;
        Tile[] tiles = layout.BuildMacro(mx, mz);
        cellCache[player.PlayerUID] = (mx, mz, tiles);
        return tiles;
    }

    // ================= Shared =================

    private bool Go(IServerPlayer player, Passage passage, Link? destination, string style = null)
    {
        // The map remembers where the threshold really leads (and the way back from there only if they arrive there);
        // someone redirected elsewhere is put down plainly, with no thin spot
        Link? real = destination;
        if (destination is { } d) destination = Redirect(player, passage, d);
        bool redirected = !Nullable.Equals(real, destination);
        if (real is { } to) Remember(player, player.Entity.Pos.XYZ, to, passage.TwoWay, arrived: !redirected);
        if (redirected && destination is { } other) destination = other with { Marker = false };
        if (!Arrive(player, destination, style, redirected ? null : passage.Source)) return false;
        if (passage.Message != null) player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get(passage.Message), EnumChatType.Notification);
        return true;
    }

    /// <summary>
    /// Where someone going through a threshold is put down after all: the far places (ids 14-20) may send them somewhere else
    /// than it leads, just before they arrive (what is written down in the network stays as it was).
    /// </summary>
    private Link Redirect(IServerPlayer player, Passage passage, Link destination) =>
        RunRedirect(player, passage, destination) ?? FunRedirect(player, passage, destination) ?? EndRedirect(player, passage, destination)
        ?? HubRedirect(player, passage, destination) ?? L974Redirect(player, passage, destination)
        ?? L3999Redirect(player, passage, destination) ?? L188Redirect(player, passage, destination)
        ?? destination;

    /// <summary>
    /// Marks on the player's map the way they just took (where they left from, and where it goes), and if they can come
    /// back the same way, the way back where they arrive. Each is marked once.
    /// </summary>
    private void Remember(IServerPlayer player, Vec3d from, Link to, bool twoWay, bool arrived = true)
    {
        string there = MapMarks.LevelName(layout, to.X, to.Z), here = MapMarks.LevelName(layout, from.X, from.Z);
        MapMarks.Add(sapi, player, from, Lang.Get(twoWay ? "backrooms:waypoint-way" : "backrooms:waypoint-oneway", there), "spiral", MapMarks.WayColor, 6, tell: false);
        if (twoWay && arrived) MapMarks.Add(sapi, player, new Vec3d(to.X, to.Y, to.Z), Lang.Get("backrooms:waypoint-back", here), "spiral", MapMarks.WayColor, 6, tell: false);
    }

    /// <summary>
    /// Walking (not being taken) from one level into the next means going through a gate in the wall between them:
    /// it is marked on the map the first time.
    /// </summary>
    private void NoticeGate(IServerPlayer player, int level, EntityPos pos)
    {
        bool known = lastSpot.TryGetValue(player.PlayerUID, out var last);
        lastSpot[player.PlayerUID] = (level, pos.X, pos.Z);
        if (!known || last.Level == level) return;
        double dx = pos.X - last.X, dz = pos.Z - last.Z;
        if (dx * dx + dz * dz > 6 * 6) return; // taken, not walked
        if (WorldLayout.IsOpenSky(level) && WorldLayout.IsOpenSky(last.Level)) return; // no wall there to have a gate in
        string a = MapMarks.LevelName(layout, last.X, last.Z), b = MapMarks.LevelName(layout, pos.X, pos.Z);
        MapMarks.Add(sapi, player, pos.XYZ, Lang.Get("backrooms:waypoint-gate", a, b), "x", MapMarks.WayColor, 16, tell: false);
    }

    /// <summary>
    /// Teleports a player to somewhere in the given level, picked by key (the <c>/backrooms goto</c> command). This
    /// is not a threshold: nothing is written down, and there is no way back.
    /// </summary>
    public bool Send(IServerPlayer player, int level, ulong key, System.Func<Tile, bool> anchor)
    {
        if (layout == null || player.Entity == null) return false;
        // Now and then the search finds nowhere to stand; try somewhere else nearby instead
        (int X, int Z)? arrival = null;
        for (int attempt = 0; attempt < 4 && arrival == null; attempt++, key = Hashing.Mix(key)) arrival = layout.FindArrival(level, key, anchor);
        if (arrival is not { } a) return Arrive(player, null);
        return Arrive(player, new Link(a.X + 0.5, geometry.FloorFor(level) + layout.ArrivalHeight(a.X, a.Z), a.Z + 0.5, false));
    }

    /// <summary>
    /// Puts a player down at a destination. <paramref name="source"/> is the threshold they came through, when they arrive
    /// where it leads (not redirected): a door or an elevator built there as its way back is seen to once they are.
    /// </summary>
    private bool Arrive(IServerPlayer player, Link? destination, string style = null, (int X, int Z)? source = null)
    {
        if (destination is not { } link)
        {
            // Nowhere to go after all: don't look again for a while
            busyUntilMs[player.PlayerUID] = sapi.World.ElapsedMilliseconds + 6000;
            return false;
        }
        if (link.Marker) inThinSpot[player.PlayerUID] = true; // they arrive standing in it
        busyUntilMs[player.PlayerUID] = sapi.World.ElapsedMilliseconds + CooldownMs;
        // Nobody walks into Level 94: you fall into it, out of a rectangle of black in the sky, and land softly on the
        // grass. (The thin spot back is on the ground; the fall is over before anyone could step back into it.)
        double drop = 0;
        int arrivalLevel = layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(link.X)), WorldLayout.MacroOf((int)Math.Floor(link.Z)));
        if (arrivalLevel == WorldLayout.Motion)
        {
            drop = Regions.MotionSystem.SkyDrop;
            busyUntilMs[player.PlayerUID] = sapi.World.ElapsedMilliseconds + CooldownMs + 6000;
            Regions.MotionSystem.LandSoftly(player.Entity, sapi.World);
        }
        // The far places (ids 14-20) see to their own arrivals
        switch (arrivalLevel)
        {
            case WorldLayout.RunLevel: RunArriving(player, link, ref drop); break;
            case WorldLayout.FunLevel: FunArriving(player, link, ref drop); break;
            case WorldLayout.TheEnd: EndArriving(player, link, ref drop); break;
            case WorldLayout.Hub: HubArriving(player, link, ref drop); break;
            case WorldLayout.Level974: L974Arriving(player, link, ref drop); break;
            case WorldLayout.Level3999: L3999Arriving(player, link, ref drop); break;
            case WorldLayout.Level188: L188Arriving(player, link, ref drop); break;
        }
        // Put down on a flight of stairs (near the top of the way back, after climbing another), they face down it,
        // and it takes them nowhere until they have stepped off it
        int ax = (int)Math.Floor(link.X), az = (int)Math.Floor(link.Z);
        Tile onto = layout.TileAt(ax, az);
        bool onStairs = onto.Stair > 0 && onto.Level == arrivalLevel;
        if (onStairs) offStairsFirst.Add(player.PlayerUID);
        else offStairsFirst.Remove(player.PlayerUID);
        // Put down on the landing of a stairwell's flight (Levels 1 and 4; at the foot of a flight up, at the top of a flight
        // down: that is never a step, so no step-off is needed), they face away from it, as if just come off it
        // (Between Levels 6 and 7, from layout version 9: at the foot of an entry room's stairs, facing into the room; on a
        // stairwell's landing, facing back up it)
        (int Dx, int Dz)? away = onStairs ? null : arrivalLevel is 1 or 4 ? network.AwayFromFlight(ax, az)
            : arrivalLevel is 6 or 7 ? network.DeepStairsFacing(ax, az) : null;
        // Put down on the Hub's narrow sidewalk, they look along the road rather than at the wall beside them
        float? look = onStairs || arrivalLevel != WorldLayout.Hub ? null : HubArrivalYaw(ax, az);
        // Put down in front of a door or an elevator built as the way back, they face away from it, as if just come out
        WayBack? wayBack = source is { } from ? network.WayBackOf(from) : null;
        if (!onStairs && away == null && wayBack is { } built) away = WayBackFacing(built);
        // The place is loaded (and if need be generated) before the player is moved; a thin spot, the way back
        // from a place with no threshold of its own, is left there once it is
        SendTransition(player, TransitionPhase.Begin, style);
        long startedMs = sapi.World.ElapsedMilliseconds;
        player.Entity.TeleportToDouble(link.X, link.Y + drop, link.Z, () =>
        {
            SendTransition(player, TransitionPhase.End, style);
            sapi.Logger.Debug("[backrooms] {0} put down at {1:0}, {2:0}, {3:0} after {4} ms ({5})", player.PlayerName, link.X, link.Y, link.Z,
                sapi.World.ElapsedMilliseconds - startedMs, style ?? "plain");
            if (link.Marker) LeaveThinSpot(link);
            if (wayBack != null) BuildWayBack(player, source.Value);
            if (onStairs) Face(player, DownFlight(onto.Pier));
            else if (away is { } d) Face(player, (float)Math.Atan2(d.Dx, d.Dz));
            else if (look is { } yaw) Face(player, yaw);
        });
        return true;
    }

    /// <summary>
    /// The yaw that looks down a flight climbing the given way. A player looks (and walks) along (sin yaw, cos yaw),
    /// so yaw 0 faces south, +z.
    /// </summary>
    private static float DownFlight(ArchPier climb) => climb switch
    {
        ArchPier.North => 0f,                  // climbs north: face south
        ArchPier.South => GameMath.PI,         // climbs south: face north
        ArchPier.West => GameMath.PIHALF,      // climbs west: face east
        _ => GameMath.PI + GameMath.PIHALF,    // climbs east: face west
    };

    /// <summary>Turns a player to face the given way (the client owns where its camera looks, so it is told).</summary>
    private void Face(IServerPlayer player, float yaw)
    {
        if (player.ConnectionState != EnumClientState.Playing || player.Entity == null) return;
        player.Entity.Pos.Yaw = yaw;
        sapi.Network.GetChannel(Channel).SendPacket(new FacePacket { Yaw = yaw }, player);
    }

    /// <summary>Makes sure the thin spot that leads back from an arrival is there.</summary>
    private void LeaveThinSpot(Link link)
    {
        if (thinSpotId == 0) return;
        IBlockAccessor blocks = sapi.World.BlockAccessor;
        var pos = new BlockPos((int)Math.Floor(link.X), (int)Math.Floor(link.Y), (int)Math.Floor(link.Z));
        // The arrival is clear floor; a tuft of grass or a loose stone may have been put there since
        for (int up = 0; up < 2; up++, pos.Up())
        {
            Block there = blocks.GetBlock(pos);
            if (there.BlockId == thinSpotId) return;
            if (there.BlockId != 0 && there.Replaceable < 5000) continue;
            blocks.SetBlock(thinSpotId, pos);
            return;
        }
        sapi.Logger.Warning("[backrooms] No room for the thin spot back from {0:0}, {1:0}, {2:0}", link.X, link.Y, link.Z);
    }

    /// <summary>Starts loading (and if need be generating) the chunk column around a place someone is about to arrive.</summary>
    private void Preload(Link at)
    {
        sapi.WorldManager.LoadChunkColumnPriority((int)at.X / GlobalConstants.ChunkSize, (int)at.Z / GlobalConstants.ChunkSize);
    }

    private static bool CanTravel(IServerPlayer player) =>
        player.ConnectionState == EnumClientState.Playing && player.Entity != null && player.Entity.Alive;

    /// <summary>The player and everyone else standing within the given distance of them.</summary>
    private List<IServerPlayer> PlayersNear(IServerPlayer player, double range)
    {
        var near = new List<IServerPlayer> { player };
        foreach (IPlayer other in sapi.World.AllOnlinePlayers)
        {
            if (other == player || other is not IServerPlayer sp || !CanTravel(sp) || IsBusy(sp)) continue;
            if (sp.Entity.Pos.SquareDistanceTo(player.Entity.Pos.XYZ) <= range * range) near.Add(sp);
        }
        return near;
    }

    private bool IsBusy(IServerPlayer player) =>
        busyUntilMs.TryGetValue(player.PlayerUID, out long until) && sapi.World.ElapsedMilliseconds < until;

    private void Play(BlockPos pos, string sound)
    {
        sapi.World.PlaySoundAt(new AssetLocation(sound), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, randomizePitch: true, range: 16);
    }
}

/// <summary>Makes a block a threshold: using it asks <see cref="ThresholdSystem"/> where it leads.</summary>
public class BlockBehaviorThreshold : BlockBehavior
{
    private string kind = "door";

    /// <summary>What kind of threshold this is (door, elevator, thinspot, ...).</summary>
    public string Kind => kind;
    private WorldInteraction[] help;

    public BlockBehaviorThreshold(Block block) : base(block)
    {
    }

    public override void Initialize(Vintagestory.API.Datastructures.JsonObject properties)
    {
        base.Initialize(properties);
        kind = properties?["kind"].AsString("door") ?? "door";
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[]
        {
            new WorldInteraction
            {
                ActionLangCode = kind switch
                {
                    "elevator" => "backrooms:blockhelp-elevator",
                    "door" or "locked" => "backrooms:blockhelp-door",
                    "thinspot" => "backrooms:blockhelp-thinspot",
                    _ => "backrooms:blockhelp-exit",
                },
                MouseButton = EnumMouseButton.Right,
            },
        };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Api is ICoreServerAPI sapi && byPlayer is IServerPlayer player)
        {
            sapi.ModLoader.GetModSystem<ThresholdSystem>().Use(player, blockSel.Position, kind);
        }
        return true;
    }
}
