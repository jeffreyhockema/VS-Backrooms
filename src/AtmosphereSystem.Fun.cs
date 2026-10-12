using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;

namespace Backrooms;

/// <summary>
/// Level Fun's air and sound on the client (kept as level 15). Its base fog is its entry in <see cref="Levels"/>: warm
/// and a little dusty. Out on an open deck the night closes in, low fog lying over the black water. The sound is the
/// hum of the lights, and under it, always, a party somewhere else: a tinny tune through two walls and a crowd's
/// murmur. The rooms' own speakers (blocks) play their tune near by, and now and then one's tape catches; on a deck
/// there is only the wind.
/// </summary>
public partial class AtmosphereSystem
{
    /// <summary>An open deck at night: dark, blue-black, a low fog over the water.</summary>
    private static readonly Atmosphere FunDeck = new(0.03f, 0.05f, 0.07f, 0.12f, 0.2f);

    private ILoadedSound funBed;
    private string funBedPlaying;
    private float funSkipClock = 40;
    private readonly BlockPos funProbe = new(0);

    /// <summary>
    /// Every tick while the player is in the level: swap <paramref name="target"/> for a part of the level with air of
    /// its own, and <paramref name="titleKey"/> for the title it is named by (lang key level-&lt;key&gt;; the level's
    /// own parts use 1501-1599).
    /// </summary>
    private void FunAir(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        if (FunOnDeck(pos)) target = FunDeck;
    }

    private bool FunOnDeck(EntityPos pos)
    {
        var zone = (FunZone)layout.TileAt((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z)).Zone;
        return zone is FunZone.Deck or FunZone.Sea;
    }

    /// <summary>Every tick, wherever the player is (<paramref name="here"/>: in the level): start and stop the level's sounds.</summary>
    private void FunSounds(float dt, EntityPos pos, bool here)
    {
        if (here) FunTapeSkip(dt, pos);
        string want = !here ? null : FunOnDeck(pos) ? "fun/deckwind" : "fun/partydistant";
        if (want == funBedPlaying) return;
        funBed?.Stop();
        funBed?.Dispose();
        funBed = null;
        funBedPlaying = want;
        if (want == null) return;
        funBed = capi.World.LoadSound(new SoundParams
        {
            Location = new AssetLocation("backrooms:sounds/ambient/" + want), ShouldLoop = true, RelativePosition = true,
            DisposeOnFinish = false, Volume = want == "fun/deckwind" ? 0.5f : 0.3f, SoundType = EnumSoundType.Ambient,
        });
        funBed?.Start();
    }

    /// <summary>Now and then the nearest speaker's tape catches: the tune slurs down and stops with a clunk.</summary>
    private void FunTapeSkip(float dt, EntityPos pos)
    {
        funSkipClock -= dt;
        if (funSkipClock > 0) return;
        funSkipClock = 50 + (float)rand.NextDouble() * 70;
        int px = (int)Math.Floor(pos.X), py = (int)Math.Floor(pos.Y), pz = (int)Math.Floor(pos.Z);
        double best = double.MaxValue;
        Vec3d at = null;
        for (int dy = -1; dy <= 4; dy++)
            for (int dz = -10; dz <= 10; dz++)
                for (int dx = -10; dx <= 10; dx++)
                {
                    Block block = capi.World.BlockAccessor.GetBlock(funProbe.Set(px + dx, py + dy, pz + dz));
                    if (block.Code?.Domain != "backrooms" || !block.Code.Path.StartsWith("fun-speaker-on-")) continue;
                    double d = dx * dx + dy * dy + dz * dz;
                    if (d < best) { best = d; at = new Vec3d(px + dx + 0.5, py + dy + 0.5, pz + dz + 0.5); }
                }
        if (at != null) capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/fun/funtune-skip"), at.X, at.Y, at.Z, null, false, 16, 0.7f);
    }
}
