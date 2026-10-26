using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;

namespace ShotBot;

/// <summary>
/// Drives the client from a text file so screenshots can be taken without anyone at the keyboard.
/// Reads SHOTBOT_DIR/commands.txt one line at a time (new lines may be appended while it runs):
///   cmd /tp =x =y =z        send any chat line
///   tp x y z                teleport (absolute block coordinates) and wait until arrived
///   tpr x yrel z            teleport, y relative to sea level (= the Level 0 floor)
///   look heading pitch      heading in compass degrees (0 N, 90 E), pitch in degrees (negative = down)
///   ready [radius]          wait until the chunks within radius blocks (default 64) are loaded, then 2.5 s
///   fov degrees
///   vd blocks               view distance
///   hud off|on
///   closeguis               closes every open dialog (confirms the character creation dialog)
///   handbook [page]         opens the handbook, and a page of it (e.g. backrooms-entities)
///   respawn                 presses the Respawn button of the death dialog
///   pause off|on
///   focus                   brings the game window to the front
///   slot n                  selects hotbar slot n (0-9), e.g. to hold a lit torch
///   daylight [off]          a clear day over the level's own air (Level 9's night, Level 10's overcast), this client only
///   wait ms
///   waitchat [ms]           wait until a chat line has arrived since the last cmd (its reply), at most ms (default 30000), then 0.5 s
///   movewait                waits until something (a goto, a threshold) has moved the player more than 50 blocks, at most 60 s
///   mark name               append "name x y z heading pitch" (where the player stands now) to marks.txt and chat.txt
///   shot name               screenshot, moved to SHOTBOT_DIR/name.png
///   mega name               2x screenshot
/// Every tick it also closes the escape menu, unpauses, and re-hides the HUD if it was asked to.
/// After every command it writes status.txt. Chat output goes to chat.txt.
/// </summary>
public class ShotBotSystem : ModSystem, IRenderer
{
    [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();

    ICoreClientAPI capi;
    string dir;
    int done;
    DateTime waitUntil = DateTime.MinValue, lastTick = DateTime.MinValue;
    string pendingShot;
    int chatLines, chatAtCmd;
    DateTime shotAt;
    bool hudHidden;
    // Someone at the keyboard pressing Escape must win: stop auto-closing after a burst of repeats
    DateTime recoverBurstStart = DateTime.MinValue; int recoverBurst; DateTime recoverMutedUntil = DateTime.MinValue;
    // pending conditions
    Func<bool> condition; DateTime conditionTimeout; string conditionName; Action onConditionMet;

    public double RenderOrder => 1;
    public int RenderRange => 1;

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Client;

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        dir = Environment.GetEnvironmentVariable("SHOTBOT_DIR") ?? Path.Combine(GamePaths.DataPath, "shotbot");
        Directory.CreateDirectory(dir);
        File.WriteAllText(Path.Combine(dir, "chat.txt"), "");
        Log("shotbot started, dir " + dir);
        api.Event.LevelFinalize += () =>
        {
            var spawn = api.World.DefaultSpawnPosition;
            File.WriteAllText(Path.Combine(dir, "ready.txt"), $"seed {api.World.Seed}\nsealevel {api.World.SeaLevel}\n"
                + (spawn == null ? "" : string.Format(CultureInfo.InvariantCulture, "spawn {0:0.##} {1:0.##} {2:0.##}\n", spawn.X, spawn.Y, spawn.Z)));
            Log("level finalized");
        };
        api.Event.ChatMessage += (int groupId, string message, EnumChatType type, string data) =>
        {
            chatLines++;
            try { File.AppendAllText(Path.Combine(dir, "chat.txt"), message + "\n"); } catch { }
        };
        api.Event.RegisterRenderer(this, EnumRenderStage.Done, "shotbot");
    }

    public void Dispose() { }

    void Log(string s)
    {
        try { File.AppendAllText(Path.Combine(dir, "log.txt"), $"{DateTime.Now:HH:mm:ss} {s}\n"); } catch { }
    }

    bool IsPaused()
    {
        var p = capi.World.GetType().GetField("IsPaused", BindingFlags.Instance | BindingFlags.Public);
        return p != null && (bool)p.GetValue(capi.World);
    }

    bool HudVisible()
    {
        var p = capi.GetType().GetProperty("HideGuis", BindingFlags.Instance | BindingFlags.Public);
        if (p == null) return true;
        return !(bool)p.GetValue(capi);
    }

    void Status()
    {
        var e = capi.World?.Player?.Entity;
        if (e == null) return;
        double heading = Heading(e);
        heading = ((heading % 360) + 360) % 360;
        string guis = string.Join(",", capi.Gui.OpenedGuis.Select(g => g.GetType().Name).Where(n => !n.StartsWith("Hud")));
        File.WriteAllText(Path.Combine(dir, "status.txt"),
            string.Format(CultureInfo.InvariantCulture, "pos {0:0.00} {1:0.00} {2:0.00}\nheading {3:0.0}\npitch {4:0.0}\nsealevel {5}\nhour {6:0.00}\ndone {7}\npaused {8}\nhud {9}\nguis {10}\n",
                e.Pos.X, e.Pos.Y, e.Pos.Z, heading, 180 - e.Pos.Pitch * 180 / Math.PI, capi.World.SeaLevel, capi.World.Calendar.HourOfDay, done, IsPaused(), HudVisible(), guis));
    }

    public void OnRenderFrame(float deltaTime, EnumRenderStage stage)
    {
        DateTime now = DateTime.UtcNow;
        if ((now - lastTick).TotalMilliseconds < 200) return;
        lastTick = now;
        try { Tick(now); }
        catch (Exception ex) { Log("tick error: " + ex); }
    }

    void Recover()
    {
        if (DateTime.UtcNow < recoverMutedUntil) return;
        bool had = false;
        foreach (var g in capi.Gui.OpenedGuis.ToArray())
        {
            string name = g.GetType().Name;
            if (name == "GuiDialogEscapeMenu" || name == "GuiDialogCreateCharacter" || name == "GuiDialogWorldMap")
            {
                if (name == "GuiDialogCreateCharacter")
                {
                    var f = g.GetType().GetField("didSelect", BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);
                    f?.SetValue(g, true);
                }
                if (g is GuiDialog d) { d.TryClose(); had = true; Log("auto-closed " + name); }
            }
        }
        if (IsPaused()) { SetPause(false); had = true; }
        if (hudHidden && HudVisible())
        {
            capi.Input.GetHotKeyByCode("togglehud")?.Handler?.Invoke(new KeyCombination());
            Log("re-hid HUD");
        }
        if (had)
        {
            Wait(500);
            if ((DateTime.UtcNow - recoverBurstStart).TotalSeconds > 20) { recoverBurstStart = DateTime.UtcNow; recoverBurst = 0; }
            if (++recoverBurst >= 3) { recoverMutedUntil = DateTime.UtcNow.AddMinutes(2); Log("escape menu keeps reopening: leaving it alone for 2 minutes"); }
        }
    }

    void Tick(DateTime now)
    {
        var e = capi.World?.Player?.Entity;
        if (e == null) return;

        Recover();

        if (pendingShot != null && (now - shotAt).TotalMilliseconds > 2500)
        {
            try
            {
                var newest = new DirectoryInfo(GamePaths.Screenshots).GetFiles("*.png").OrderByDescending(f => f.LastWriteTimeUtc).FirstOrDefault();
                if (newest != null && (DateTime.UtcNow - newest.LastWriteTimeUtc).TotalSeconds < 30)
                {
                    string dest = Path.Combine(dir, pendingShot + ".png");
                    if (File.Exists(dest)) File.Delete(dest);
                    newest.MoveTo(dest);
                    Log($"shot {pendingShot} <- {newest.Name}");
                }
                else Log($"shot {pendingShot}: no fresh screenshot file found");
            }
            catch (Exception ex) { Log("shot move failed: " + ex.Message); }
            pendingShot = null;
        }

        if (now < waitUntil || pendingShot != null) return;

        if (condition != null)
        {
            if (condition())
            {
                Log($"  {conditionName}: met");
                var act = onConditionMet; condition = null; onConditionMet = null;
                act?.Invoke();
            }
            else if (now > conditionTimeout)
            {
                Log($"  {conditionName}: TIMEOUT");
                condition = null; onConditionMet = null;
            }
            else return;
            if (now < waitUntil) return;
        }

        string cmdFile = Path.Combine(dir, "commands.txt");
        if (!File.Exists(cmdFile)) return;
        string[] lines;
        try { lines = File.ReadAllLines(cmdFile); } catch { return; }
        if (done >= lines.Length) return;
        string line = lines[done++].Trim();
        if (line.Length == 0 || line.StartsWith("#")) { Status(); return; }
        Log("> " + line);
        try { Run(line, e); }
        catch (Exception ex) { Log("error: " + ex); }
        Status();
    }

    static double D(string s) => double.Parse(s, CultureInfo.InvariantCulture);
    /// <summary>The compass heading the player looks along (0 north, 90 east), from its yaw (the inverse of the look command).</summary>
    static double Heading(EntityPlayer e) => ((180 - e.Pos.Yaw * 180 / Math.PI) % 360 + 360) % 360;
    void Wait(int ms) => waitUntil = DateTime.UtcNow.AddMilliseconds(ms);

    void WaitFor(string name, Func<bool> cond, int timeoutMs, Action then = null)
    {
        conditionName = name; condition = cond; conditionTimeout = DateTime.UtcNow.AddMilliseconds(timeoutMs); onConditionMet = then;
    }

    bool ChunksLoaded(int radius)
    {
        var e = capi.World.Player.Entity;
        var ba = capi.World.BlockAccessor;
        int y = (int)e.Pos.Y;
        for (int dz = -radius; dz <= radius; dz += 32)
            for (int dx = -radius; dx <= radius; dx += 32)
                if (ba.GetChunkAtBlockPos((int)e.Pos.X + dx, y, (int)e.Pos.Z + dz) == null) return false;
        return true;
    }

    void CloseGuis()
    {
        foreach (var g in capi.Gui.OpenedGuis.ToArray())
        {
            string name = g.GetType().Name;
            if (name == "GuiDialogCreateCharacter")
            {
                var f = g.GetType().GetField("didSelect", BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);
                if (f != null) f.SetValue(g, true);
            }
            if (g is GuiDialog d && !(name.StartsWith("Hud")))
            {
                d.TryClose();
                Log("closed " + name);
            }
        }
    }

    void SetPause(bool paused)
    {
        var m = capi.World.GetType().GetMethod("PauseGame", BindingFlags.Instance | BindingFlags.Public);
        if (m == null) { Log("PauseGame not found on " + capi.World.GetType().Name); return; }
        m.Invoke(capi.World, new object[] { paused });
        Log("pause " + paused);
    }

    void Teleport(double x, double y, double z)
    {
        capi.SendChatMessage(string.Format(CultureInfo.InvariantCulture, "/tp ={0} ={1} ={2}", x, y, z));
        var e = capi.World.Player.Entity;
        WaitFor("arrive", () => Math.Abs(e.Pos.X - x) < 2 && Math.Abs(e.Pos.Z - z) < 2 && Math.Abs(e.Pos.Y - y) < 3, 20000, () => Wait(300));
    }

    void Run(string line, EntityPlayer e)
    {
        string[] p = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        switch (p[0])
        {
            case "cmd":
                chatAtCmd = chatLines;
                capi.SendChatMessage(line.Substring(4));
                Wait(600);
                break;
            case "tp":
                Teleport(D(p[1]), D(p[2]), D(p[3]));
                break;
            case "tpr":
                Teleport(D(p[1]), D(p[2]) + capi.World.SeaLevel, D(p[3]));
                break;
            case "look":
            {
                // The client keeps its own mouse yaw/pitch and writes them into the entity every frame.
                // Pitch runs from ~91 deg (straight up) through 180 (level) to ~269 (straight down). Compass heading h
                // is yaw pi - h (checked against the layout harness on 2026-10-13; the -h used before looked the opposite way).
                float yaw = GameMath.Mod((float)(Math.PI - D(p[1]) * Math.PI / 180), (float)(Math.PI * 2));
                float pitch = (float)(Math.PI - D(p[2]) * Math.PI / 180);
                capi.Input.MouseYaw = yaw; capi.Input.MousePitch = pitch;
                e.Pos.Yaw = yaw; e.Pos.Pitch = pitch;
                e.BodyYaw = yaw; e.BodyYawServer = yaw;
                e.Pos.HeadYaw = 0; e.Pos.HeadPitch = 0;
                Wait(150);
                break;
            }
            case "movewait":
            {
                // waits until something (a goto, a threshold) has moved the player more than 50 blocks
                double sx = e.Pos.X, sz = e.Pos.Z;
                WaitFor("moved", () => Math.Abs(e.Pos.X - sx) + Math.Abs(e.Pos.Z - sz) > 50, 60000, () => Wait(500));
                break;
            }
            case "ready":
            {
                int radius = p.Length > 1 ? (int)D(p[1]) : 64;
                WaitFor($"chunks within {radius}", () => ChunksLoaded(radius), 60000, () => Wait(2500));
                break;
            }
            case "fov":
                capi.Settings.Int["fieldOfView"] = (int)D(p[1]);
                break;
            case "vd":
                capi.Settings.Int["viewDistance"] = (int)D(p[1]);
                break;
            case "hud":
            {
                bool want = p[1] == "off";
                hudHidden = want;
                if (want == HudVisible())
                    capi.Input.GetHotKeyByCode("togglehud")?.Handler?.Invoke(new KeyCombination());
                break;
            }
            case "closeguis":
                CloseGuis();
                Wait(300);
                break;
            case "pause":
                SetPause(p[1] == "on");
                Wait(300);
                break;
            case "respawn":
            {
                // Presses the Respawn button of the death dialog (the player stays dead until someone does)
                foreach (var g in capi.Gui.OpenedGuis.ToArray())
                {
                    if (g.GetType().Name != "GuiDialogDead") continue;
                    var m = g.GetType().GetMethod("OnRespawn", BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);
                    Log("respawn: " + (m == null ? "no OnRespawn" : "pressed"));
                    m?.Invoke(g, null);
                }
                Wait(500);
                break;
            }
            case "handbook":
            {
                // handbook            opens the handbook
                // handbook <code>     opens a page of it (e.g. backrooms-entities; the handbook has to have been opened once)
                var hb = capi.ModLoader.Systems.FirstOrDefault(m => m.GetType().Name == "ModSystemSurvivalHandbook");
                var dlg = hb?.GetType().GetField("dialog", BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public)?.GetValue(hb) as GuiDialog;
                if (dlg == null) { Log("handbook: dialog not found"); break; }
                if (!dlg.IsOpened()) { dlg.TryOpen(); Wait(2500); }
                if (p.Length > 1)
                {
                    var open = dlg.GetType().GetMethod("OpenDetailPageFor", BindingFlags.Instance | BindingFlags.Public);
                    Log("handbook page " + p[1] + ": " + (open == null ? "no OpenDetailPageFor" : open.Invoke(dlg, new object[] { p[1] })));
                    Wait(1500);
                }
                break;
            }
            case "focus":
            {
                IntPtr h = System.Diagnostics.Process.GetCurrentProcess().MainWindowHandle;
                Log("focus: " + (h == IntPtr.Zero ? "no handle" : SetForegroundWindow(h).ToString()));
                Wait(500);
                break;
            }
            case "daylight":
            {
                // A clear day over whatever the level's own air says (Level 9's endless night, Level 10's overcast), for
                // an alternative shot: added last at weight 1, it wins over the Backrooms' ambient modifiers. Since 0.513.3
                // the mod moves its level's air to the end every tick and keeps only its own clear-air cheat after it, so
                // the daylight goes in under that cheat's key (CheatSystem.ClearAirKey) to stay last
                const string key = "backrooms-cheat-clearair";
                capi.Ambient.CurrentModifiers.Remove(key);
                if (p.Length < 2 || p[1] != "off")
                {
                    var day = new AmbientModifier().EnsurePopulated();
                    day.FogColor = WeightedFloatArray.New(new[] { 0.80f, 0.86f, 0.95f }, 1);
                    day.FogDensity = WeightedFloat.New(0.0012f, 1);
                    day.FogMin = WeightedFloat.New(0, 1);
                    day.FlatFogDensity = WeightedFloat.New(0, 1);
                    day.FogBrightness = WeightedFloat.New(1, 1);
                    day.SceneBrightness = WeightedFloat.New(1, 1);
                    day.CloudBrightness = WeightedFloat.New(1, 1);
                    day.CloudDensity = WeightedFloat.New(0.1f, 1);
                    capi.Ambient.CurrentModifiers[key] = day;
                }
                Wait(500);
                break;
            }
            case "slot":
            {
                // Selects a hotbar slot, e.g. one holding a lit torch (a held light lights the scene)
                var inv = capi.World.Player.InventoryManager;
                inv.ActiveHotbarSlotNumber = (int)D(p[1]);
                Log("holding " + (inv.ActiveHotbarSlot?.Itemstack?.Collectible?.Code?.ToString() ?? "nothing"));
                Wait(300);
                break;
            }
            case "wait":
                Wait((int)D(p[1]));
                break;
            case "waitchat":
            {
                int seen = chatAtCmd;
                WaitFor("chat", () => chatLines > seen, p.Length > 1 ? (int)D(p[1]) : 30000, () => Wait(500));
                break;
            }
            case "mark":
            {
                double heading = Heading(e);
                string m = string.Format(CultureInfo.InvariantCulture, "{0} {1:0.00} {2:0.00} {3:0.00} {4:0.0} {5:0.0}", p.Length > 1 ? p[1] : "-",
                    e.Pos.X, e.Pos.Y, e.Pos.Z, heading, 180 - e.Pos.Pitch * 180 / Math.PI);
                try { File.AppendAllText(Path.Combine(dir, "marks.txt"), m + "\n"); File.AppendAllText(Path.Combine(dir, "chat.txt"), "#mark " + m + "\n"); } catch { }
                Log("mark " + m);
                break;
            }
            case "shot":
            case "mega":
                capi.Input.GetHotKeyByCode(p[0] == "mega" ? "megascreenshot" : "screenshot")?.Handler?.Invoke(new KeyCombination());
                pendingShot = p[1];
                shotAt = DateTime.UtcNow;
                Log(string.Format(CultureInfo.InvariantCulture, "  at {0:0.0} {1:0.0} {2:0.0} heading {3:0} pitch {4:0}", e.Pos.X, e.Pos.Y, e.Pos.Z,
                    Heading(e), 180 - e.Pos.Pitch * 180 / Math.PI));
                break;
            default:
                Log("unknown command " + p[0]);
                break;
        }
    }
}
