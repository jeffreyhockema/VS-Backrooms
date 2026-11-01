using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Regions;

/// <summary>
/// Level 52's clock (experimental): keeps <see cref="WorldLayout.L52Hours"/>, the hour the level's weather (its drifting
/// temperature, 10 to 32 °C) is worked out for, up to date from the world's calendar, on the server and the client. Also the
/// dev test of the level's ways in and back, <c>/backrooms l52 waytest school|exit|x z</c> (ThresholdSystem.L52.cs).
/// </summary>
public class L52System : ModSystem
{
    // (After BackroomsModSystem, which makes the backrooms command)
    public override double ExecuteOrder() => 1.3;

    public override void Start(ICoreAPI api)
    {
        if (api is ICoreServerAPI sapi) sapi.Event.RegisterGameTickListener(_ => WorldLayout.L52Hours = api.World.Calendar.TotalHours, 2000, 500);
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        CommandArgumentParsers parsers = api.ChatCommands.Parsers;
        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("l52")
                .WithDescription("Level 52 (testing): 'waytest school', 'waytest exit' or 'waytest x z' goes in by the high school or the EMERGENCY EXIT nearest spawn "
                    + "(or the door at x z) and back out through the campus door beside the arrival, and says where each leads (run it twice: the first may only load chunks)")
                .WithArgs(parsers.Word("what"), parsers.OptionalWord("where"), parsers.OptionalInt("x"), parsers.OptionalInt("z"))
                .RequiresPrivilege(Privilege.controlserver)
                .HandleWith(args =>
                {
                    if (((string)args[0])?.Trim() != "waytest") return TextCommandResult.Error("waytest school|exit|x z");
                    string where = ((args[1] as string) ?? "school").Trim();
                    int x = 0, z = 0;
                    if (int.TryParse(where, out int px)) { x = px; z = args[2] is int pz ? pz : 0; where = "at"; }
                    string text = api.ModLoader.GetModSystem<Thresholds.ThresholdSystem>()?.L52WayTest(where, x, z) ?? "no threshold system";
                    api.Logger.Notification("[backrooms] l52 waytest: {0}", text);
                    return TextCommandResult.Success(text);
                })
            .EndSubCommand();
    }
}

/// <summary>
/// Level 52's sun (experimental): "the sun is the only celestial light". The outside sky is hidden there
/// (AtmosphereSystem.L52.cs), so this draws the sun instead: a warm white disc with its glow (textures/environment/l52-sun.png,
/// made by tools/gen_52.py) always in the same place, high in the south-south-east, the same for every player at every hour,
/// a little dimmer while it is night on Terra. It is drawn just inside the view distance, scaled so it always looks the
/// same size, unfogged and glowing (as Regions.L73Moon draws Level 73's moon).
/// </summary>
public class L52Sun : ModSystem, IRenderer
{
    /// <summary>Where the sun hangs: its bearing (degrees clockwise from north), its height above the horizon, and its size with its glow (degrees across).</summary>
    private const double Bearing = 160, Elevation = 58, Across = 9;

    /// <summary>How far off it is drawn, as a share of the view distance.</summary>
    private const float DrawnAt = 0.6f;

    private ICoreClientAPI capi;
    private WorldLayout layout;
    private MeshRef mesh;
    private int texture;
    private readonly Matrixf model = new();

    public double RenderOrder => 0.44;
    public int RenderRange => 0;

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Client;

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        api.Event.LevelFinalize += OnLevelFinalize;
    }

    private void OnLevelFinalize()
    {
        if (!BackroomsWorld.IsBackroomsClimate(capi.World.Config)) return;
        layout = BackroomsWorld.CreateLayout(capi.World);
        var data = new MeshData(4, 6, false, true, true, true);
        data.AddVertex(-0.5f, -0.5f, 0, 0, 1, ColorUtil.WhiteArgb);
        data.AddVertex(0.5f, -0.5f, 0, 1, 1, ColorUtil.WhiteArgb);
        data.AddVertex(0.5f, 0.5f, 0, 1, 0, ColorUtil.WhiteArgb);
        data.AddVertex(-0.5f, 0.5f, 0, 0, 0, ColorUtil.WhiteArgb);
        data.AddIndices(0, 1, 2, 0, 2, 3);
        mesh = capi.Render.UploadMesh(data);
        texture = capi.Render.GetOrLoadTexture(new AssetLocation("backrooms", "textures/environment/l52-sun.png"));
        capi.Event.RegisterRenderer(this, EnumRenderStage.Opaque, "backrooms-l52-sun");
    }

    public void OnRenderFrame(float deltaTime, EnumRenderStage stage)
    {
        EntityPlayer player = capi.World.Player?.Entity;
        if (player == null || mesh == null || texture <= 0) return;
        int px = (int)Math.Floor(player.Pos.X), py = (int)Math.Floor(player.Pos.Y), pz = (int)Math.Floor(player.Pos.Z);
        if (layout.LevelAt(WorldLayout.MacroOf(px), WorldLayout.MacroOf(pz)) != WorldLayout.Level52) return;
        WorldLayout.L52Hours = capi.World.Calendar.TotalHours;

        double b = Bearing * Math.PI / 180, e = Elevation * Math.PI / 180;
        double dx = Math.Sin(b) * Math.Cos(e), dy = Math.Sin(e), dz = -Math.Cos(b) * Math.Cos(e);
        float distance = DrawnAt * Math.Max(64, capi.Settings.Int["viewDistance"]);
        float size = (float)(2 * distance * Math.Tan(Across * Math.PI / 360));
        double hour = capi.World.Calendar.HourOfDay;
        float bright = 1f - 0.15f * (float)GameMath.Clamp(Math.Cos((hour - 0.5) / 24 * Math.PI * 2) * 1.5 - 0.3, 0, 1);

        IRenderAPI render = capi.Render;
        IStandardShaderProgram prog = render.PreparedStandardShader(px, py + 1, pz);
        prog.Tex2D = texture;
        prog.NormalShaded = 0;
        prog.DontWarpVertices = 1;
        prog.ExtraGlow = 255;
        prog.AlphaTest = 0.02f;
        prog.FogMinIn = 0;
        prog.FogDensityIn = 0;
        prog.RgbaAmbientIn = new Vec3f(bright, bright, bright);
        prog.RgbaLightIn = new Vec4f(bright, bright, bright, 1);
        render.GlToggleBlend(true);
        model.Identity().Translate((float)(dx * distance), (float)(dy * distance), (float)(dz * distance))
            .RotateY((float)Math.Atan2(-dx, -dz)).RotateX((float)e).Scale(size, size, size);
        prog.ModelMatrix = model.Values;
        prog.ViewMatrix = render.CameraMatrixOriginf;
        prog.ProjectionMatrix = render.CurrentProjectionMatrix;
        render.GlDisableCullFace();
        render.RenderMesh(mesh);
        render.GlEnableCullFace();
        prog.Stop();
    }

    public override void Dispose()
    {
        if (capi != null)
        {
            capi.Event.UnregisterRenderer(this, EnumRenderStage.Opaque);
            mesh?.Dispose();
        }
        base.Dispose();
    }
}
