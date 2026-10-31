using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;

namespace Backrooms.Regions;

/// <summary>
/// Level 73's moon (experimental): "a full moon hangs fixed and lights the ground". The outside sky is hidden there
/// (AtmosphereSystem.L73.cs), so this draws the moon instead: a pale disc (textures/environment/l73-moon.png, made by
/// tools/gen_73.py) always in the same place in the sky, low over the sea to the south-south-west, the same for every
/// player at every hour. It is drawn just inside the view distance, scaled so it always looks the same size, unfogged
/// and glowing, and goes when black cloud covers it (<see cref="AtmosphereSystem.L73DarkSpell"/>).
/// </summary>
public class L73Moon : ModSystem, IRenderer
{
    /// <summary>Where the moon hangs: its bearing (degrees clockwise from north) and height above the horizon, and its size (degrees across).</summary>
    private const double Bearing = 10, Elevation = 18, Across = 5;

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
        // A unit quad about its middle, facing south (toward +z)
        var data = new MeshData(4, 6, false, true, true, true);
        data.AddVertex(-0.5f, -0.5f, 0, 0, 1, ColorUtil.WhiteArgb);
        data.AddVertex(0.5f, -0.5f, 0, 1, 1, ColorUtil.WhiteArgb);
        data.AddVertex(0.5f, 0.5f, 0, 1, 0, ColorUtil.WhiteArgb);
        data.AddVertex(-0.5f, 0.5f, 0, 0, 0, ColorUtil.WhiteArgb);
        data.AddIndices(0, 1, 2, 0, 2, 3);
        mesh = capi.Render.UploadMesh(data);
        texture = capi.Render.GetOrLoadTexture(new AssetLocation("backrooms", "textures/environment/l73-moon.png"));
        capi.Event.RegisterRenderer(this, EnumRenderStage.Opaque, "backrooms-l73-moon");
    }

    public void OnRenderFrame(float deltaTime, EnumRenderStage stage)
    {
        EntityPlayer player = capi.World.Player?.Entity;
        if (player == null || mesh == null || texture <= 0) return;
        int px = (int)Math.Floor(player.Pos.X), py = (int)Math.Floor(player.Pos.Y), pz = (int)Math.Floor(player.Pos.Z);
        if (layout.LevelAt(WorldLayout.MacroOf(px), WorldLayout.MacroOf(pz)) != WorldLayout.Level73) return;
        float covered = AtmosphereSystem.L73DarkSpell(capi.World.Seed, capi.World.Calendar.TotalHours);
        if (covered > 0.5f) return;

        // The direction to it, and a disc of the size it should look at the distance it is drawn
        double b = Bearing * Math.PI / 180, e = Elevation * Math.PI / 180;
        double dx = Math.Sin(b) * Math.Cos(e), dy = Math.Sin(e), dz = -Math.Cos(b) * Math.Cos(e);
        float distance = DrawnAt * Math.Max(64, capi.Settings.Int["viewDistance"]);
        float size = (float)(2 * distance * Math.Tan(Across * Math.PI / 360));

        IRenderAPI render = capi.Render;
        IStandardShaderProgram prog = render.PreparedStandardShader(px, py + 1, pz);
        prog.Tex2D = texture;
        prog.NormalShaded = 0;
        prog.DontWarpVertices = 1;
        prog.ExtraGlow = 255;
        prog.AlphaTest = 0.5f;
        prog.FogMinIn = 0;
        prog.FogDensityIn = 0;
        prog.RgbaAmbientIn = new Vec3f(1, 1, 1);
        prog.RgbaLightIn = new Vec4f(1, 1, 1, 1);
        // Turned to face the eye: about the vertical toward its bearing, then tipped up to its height
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
