using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;

namespace Backrooms.Regions;

/// <summary>
/// Level 94's landmark: the white castle on its glass mountain, on the horizon from anywhere in the hills ("a floating
/// castle", "a 'Transparent Mountain'"). Arrivals land 250 to 750 blocks from it, so that the way the houses come
/// apart points to it; but the game draws nothing past the view distance (256 to 512 for most players), so from most
/// of the hills the real castle is never there to see.
///
/// Past the view distance this draws a picture of it instead (textures/environment/motioncastle-far.png, made by
/// tools/gen_motion.py): turned to face the player, scaled down and brought in to just inside the view distance, so it
/// stands on the horizon at exactly the size and place the castle would, behind the hills that are nearer. It is
/// fogged as though it were as far off as the castle really is, and glows a little, like the castle's own walls, so it
/// still stands out at dusk. Nearer than that, the castle itself is in sight and the picture is not drawn (where they
/// meet, the two are the same size in the same place).
/// </summary>
public class MotionLandmark : ModSystem, IRenderer
{
    /// <summary>The picture's size in blocks: the mountain's foot across, and up to the tips of the towers' roofs.</summary>
    private const float HalfWidth = WorldLayout.MountainRadius, Height = 64;

    /// <summary>
    /// How far off the picture is drawn, as a share of the view distance (the game fades out whatever is drawn further
    /// than about 0.8 of it, counting the picture's corners).
    /// </summary>
    private const float DrawnAt = 0.7f;

    /// <summary>How much it glows (out of 255), like the castle's walls.</summary>
    private const int Glow = 110;

    private ICoreClientAPI capi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private MeshRef mesh;
    private int texture;
    private readonly Matrixf model = new();

    public double RenderOrder => 0.45;
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
        geometry = BackroomsWorld.CreateGeometry(capi.World);
        // A quad standing on its foot, the picture's top at v = 0
        var data = new MeshData(4, 6, false, true, true, true);
        data.AddVertex(-HalfWidth, 0, 0, 0, 1, ColorUtil.WhiteArgb);
        data.AddVertex(HalfWidth, 0, 0, 1, 1, ColorUtil.WhiteArgb);
        data.AddVertex(HalfWidth, Height, 0, 1, 0, ColorUtil.WhiteArgb);
        data.AddVertex(-HalfWidth, Height, 0, 0, 0, ColorUtil.WhiteArgb);
        data.AddIndices(0, 1, 2, 0, 2, 3);
        mesh = capi.Render.UploadMesh(data);
        texture = capi.Render.GetOrLoadTexture(new AssetLocation("backrooms", "textures/environment/motioncastle-far.png"));
        capi.Event.RegisterRenderer(this, EnumRenderStage.Opaque, "backrooms-castle-far");
        registered = true;
    }

    // (Set once the renderer is registered: in a world that is not the Backrooms, it never is)
    private bool registered;

    public void OnRenderFrame(float deltaTime, EnumRenderStage stage)
    {
        EntityPlayer player = capi.World.Player?.Entity;
        if (player == null || mesh == null || texture <= 0) return;
        int px = (int)Math.Floor(player.Pos.X), py = (int)Math.Floor(player.Pos.Y), pz = (int)Math.Floor(player.Pos.Z);
        if (layout.LevelAt(WorldLayout.MacroOf(px), WorldLayout.MacroOf(pz)) != WorldLayout.Motion) return;

        Vec3d cam = player.CameraPos;
        double dx = layout.MotionOriginX + 0.5 - cam.X, dz = layout.MotionOriginZ + 0.5 - cam.Z;
        double dy = geometry.FloorFor(WorldLayout.Motion) + 1 - cam.Y;
        double distance = Math.Sqrt(dx * dx + dz * dz), drawn = DrawnAt * Math.Max(64, capi.Settings.Int["viewDistance"]);
        if (distance <= drawn) return;

        // Scaled toward the eye, it covers just what the castle would
        float s = (float)(drawn / distance);
        IRenderAPI render = capi.Render;
        IStandardShaderProgram prog = render.PreparedStandardShader(px, py + 1, pz);
        prog.Tex2D = texture;
        prog.NormalShaded = 0;
        prog.DontWarpVertices = 1;
        prog.ExtraGlow = Glow;
        prog.AlphaTest = 0.5f;
        // Fogged for where the castle stands, not where the picture is (the game counts fog out to 250 blocks at most)
        float density = capi.Ambient.BlendedFogDensity;
        double fogThere = 1 - Math.Exp(-density * distance), fogHere = 1 - Math.Exp(-density * Math.Min(250, drawn));
        prog.FogMinIn = capi.Ambient.BlendedFogMin + (float)Math.Max(0, fogThere - fogHere);
        model.Identity().Translate((float)(dx * s), (float)(dy * s), (float)(dz * s)).RotateY((float)Math.Atan2(-dx, -dz)).Scale(s, s, s);
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
            capi.Event.LevelFinalize -= OnLevelFinalize;
            if (registered) capi.Event.UnregisterRenderer(this, EnumRenderStage.Opaque);
            mesh?.Dispose();
        }
        base.Dispose();
    }
}
