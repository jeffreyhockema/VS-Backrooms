using System;
using System.Collections.Generic;
using System.Text;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Regions;

/// <summary>
/// Level 23's buried sentries (experimental, kept as level 28): faces in the bark (the l23-sentry blocks the generator sets
/// into some trunks). After the Wikidot page: say "it's only a matter of time" near one and it screams, "like rusty chainsaws
/// cutting wood", loud enough to burst eardrums. Here: the phrase said in chat, in the level, within 12 blocks of a sentry,
/// sets off every sentry that near (the scream is heard a long way off), and everyone within 10 blocks of a screaming one
/// takes a blow and is told their ears are ringing. Nothing else in the mod reads chat. This file is the level's own.
/// </summary>
public class L23Sentries : ModSystem
{
    private const int Reach = 12;
    private const double HurtReach = 10;
    private const float Blow = 3f;
    private const string Phrase = "only a matter of time";
    /// <summary>A player's watched int, 1 once sentries have screamed at them (the handbook then counts them met).</summary>
    public const string ScreamedKey = "backrooms:l23Screamed";

    private ICoreServerAPI sapi;
    private WorldLayout layout;

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            api.Event.PlayerChat += OnChat;
        });
    }

    /// <summary>The words of a message, lower case, with the apostrophes and punctuation gone and the spaces single.</summary>
    private static string Plain(string message)
    {
        var sb = new StringBuilder(message.Length);
        bool space = true, tag = false;
        foreach (char ch in message)
        {
            if (ch == '<') tag = true;
            if (tag) { if (ch == '>') tag = false; continue; }
            if (char.IsLetter(ch)) { sb.Append(char.ToLowerInvariant(ch)); space = false; }
            else if (ch is '\'' or '’') continue;
            else if (!space) { sb.Append(' '); space = true; }
        }
        return sb.ToString();
    }

    private void OnChat(IServerPlayer player, int channelId, ref string message, ref string data, BoolRef consumed)
    {
        if (layout == null || message == null || player?.Entity == null) return;
        if (!Plain(message).Contains(Phrase, StringComparison.Ordinal)) return;
        var pos = player.Entity.Pos;
        int px = (int)Math.Floor(pos.X), py = (int)Math.Floor(pos.Y), pz = (int)Math.Floor(pos.Z);
        if (layout.LevelAt(WorldLayout.MacroOf(px), WorldLayout.MacroOf(pz)) != WorldLayout.Level23) return;

        // The sentries in earshot
        IBlockAccessor ba = sapi.World.BlockAccessor;
        var at = new BlockPos(0);
        var screaming = new List<Vec3d>();
        for (int dy = -6; dy <= 6; dy++)
            for (int dz = -Reach; dz <= Reach; dz++)
                for (int dx = -Reach; dx <= Reach; dx++)
                {
                    if (dx * dx + dz * dz > Reach * Reach) continue;
                    Block block = ba.GetBlock(at.Set(px + dx, py + dy, pz + dz));
                    if (block?.Code == null || block.Code.Domain != "backrooms" || !block.Code.Path.StartsWith("l23-sentry", StringComparison.Ordinal)) continue;
                    screaming.Add(new Vec3d(px + dx + 0.5, py + dy + 0.5, pz + dz + 0.5));
                }
        if (screaming.Count == 0) return;

        var scream = new AssetLocation("backrooms:sounds/ambient/23/sentryscream");
        for (int i = 0; i < Math.Min(3, screaming.Count); i++)
            sapi.World.PlaySoundAt(scream, screaming[i].X, screaming[i].Y, screaming[i].Z, null, randomizePitch: true, range: 96, volume: 1f);
        // Everyone close enough: a blow, and their ears ringing
        foreach (IPlayer other in sapi.World.AllOnlinePlayers)
        {
            if (other.Entity is not { Alive: true } e || other is not IServerPlayer sp) continue;
            bool near = false;
            foreach (Vec3d s in screaming) near |= e.Pos.XYZ.SquareDistanceTo(s) < HurtReach * HurtReach;
            if (!near) continue;
            e.ReceiveDamage(new DamageSource { Source = EnumDamageSource.Block, Type = EnumDamageType.Injury, SourcePos = screaming[0] }, Blow);
            // (The handbook's "met" for the sentries, which are blocks: config/guide.json's playerAttribute)
            e.WatchedAttributes.SetInt(ScreamedKey, 1);
            sp.SendMessage(Vintagestory.API.Config.GlobalConstants.GeneralChatGroup, Say.T(sp, "backrooms:l23-sentry-scream"), EnumChatType.Notification);
        }
        sapi.Logger.Notification("[backrooms] Level 23: {0} said it near {1} sentries", player.PlayerName, screaming.Count);
    }
}
