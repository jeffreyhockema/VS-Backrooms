using System;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Map;

/// <summary>
/// Wanderers' notes: scraps of paper left by those who came before, each telling of one thing near where it is read.
/// A note of a door tells of the nearest gate out of the level; of a way, the nearest elevator, stairwell or pit; of
/// a cache, the nearest box or crate nobody has opened; of a refuge, the nearest safe place or wanderer who trades.
/// Reading one marks the place on the map and uses the note up. One that tells of nothing near is kept.
/// </summary>
public class WayfindingSystem : ModSystem
{
    private ICoreServerAPI sapi;
    private WorldLayout layout;

    public override void Start(ICoreAPI api)
    {
        api.RegisterItemClass("BackroomsWandererNote", typeof(ItemWandererNote));
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType == BackroomsWorld.WorldTypeCode) layout = BackroomsWorld.CreateLayout(api.World);
        });
    }

    /// <summary>Reads a note of the given kind where the player stands. Returns whether it told them of anything.</summary>
    public bool Read(IServerPlayer player, string kind)
    {
        if (layout == null) return false;
        EntityPos pos = player.Entity.Pos;
        int x = (int)Math.Floor(pos.X), z = (int)Math.Floor(pos.Z);
        int level = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z));

        (int X, int Z)? found = null;
        string title = null, icon = "x";
        switch (kind)
        {
            case "door":
                // Out to the next level if there is a gate that way, otherwise any gate out
                var gate = layout.NearestGate(x, z, level, 1200, level + 1) ?? layout.NearestGate(x, z, level, 1200);
                if (gate is { } g)
                {
                    found = (g.X, g.Z);
                    title = Lang.Get("backrooms:waypoint-note-door", Lang.Get("backrooms:levelname", g.To));
                }
                break;
            case "way":
                found = layout.NearestThreshold(x, z, level, 320);
                title = Lang.Get("backrooms:waypoint-note-way");
                icon = "spiral";
                break;
            case "cache":
                found = layout.NearestCache(x, z, level, 256);
                title = Lang.Get("backrooms:waypoint-note-cache");
                icon = "vessel";
                break;
            case "refuge":
                found = layout.NearestRefuge(x, z, level, 1600);
                title = Lang.Get("backrooms:waypoint-note-refuge");
                icon = "star1";
                break;
        }

        if (found is not { } at)
        {
            player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:note-nothing"), EnumChatType.Notification);
            return false;
        }
        double dx = at.X + 0.5 - pos.X, dz = at.Z + 0.5 - pos.Z;
        int variant = (int)(Hashing.Hash((ulong)sapi.World.Seed, at.X, at.Z, 0x707E) % 3) + 1;
        player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get($"backrooms:note-{kind}-{variant}", Direction(dx, dz), Paces(dx, dz)), EnumChatType.Notification);
        MapMarks.Add(sapi, player, new Vec3d(at.X + 0.5, pos.Y, at.Z + 0.5), title, icon, MapMarks.NoteColor, 4);
        return true;
    }

    /// <summary>The compass direction of an offset, in words (north is -Z).</summary>
    private static string Direction(double dx, double dz)
    {
        string[] names = { "e", "se", "s", "sw", "w", "nw", "n", "ne" };
        double angle = Math.Atan2(dz, dx);
        int octant = (int)Math.Round(angle / (Math.PI / 4));
        return Lang.Get("backrooms:dir-" + names[((octant % 8) + 8) % 8]);
    }

    /// <summary>The distance, rounded the way someone pacing it out would give it.</summary>
    private static int Paces(double dx, double dz)
    {
        double d = Math.Sqrt(dx * dx + dz * dz);
        int step = d < 60 ? 10 : d < 300 ? 25 : 50;
        return Math.Max(step, (int)Math.Round(d / step) * step);
    }
}

/// <summary>A wanderer's note: right-click to read it. Its kind is its variant (door, way, cache, refuge).</summary>
public class ItemWandererNote : Item
{
    public override void OnHeldInteractStart(ItemSlot slot, EntityAgent byEntity, BlockSelection blockSel, EntitySelection entitySel, bool firstEvent, ref EnumHandHandling handling)
    {
        if (!firstEvent) return;
        handling = EnumHandHandling.PreventDefault;
        if (api.Side != EnumAppSide.Server || (byEntity as EntityPlayer)?.Player is not IServerPlayer player) return;
        string kind = Variant["kind"];
        if (!api.ModLoader.GetModSystem<WayfindingSystem>().Read(player, kind)) return;
        byEntity.World.PlaySoundAt(new AssetLocation("game:sounds/effect/writing"), byEntity, null, randomizePitch: true, range: 8);
        slot.TakeOut(1);
        slot.MarkDirty();
    }
}
