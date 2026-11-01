using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;

namespace Backrooms.Regions;

/// <summary>
/// Level 47's night sky (experimental). Wikidot: "Each night, however, the fog will disperse without fail to reveal a full
/// moon. This moon appears visually identical to the Moon from The Frontrooms, albeit several times closer and with the far
/// side facing towards Level 47. Stars and the Milky Way are visible as well, but do not match any constellations visible
/// from The Frontrooms. Though rare, silvery-white auroras have been seen on occasion." The outside sky is hidden in the
/// level (a sphere of fog, AtmosphereSystem.L47.cs), so this draws its own: a dome of stars and a Milky Way of no sky of
/// ours (textures/environment/l47-stars.png), the Moon's far side, full and huge, rising in the east at dusk, high in the
/// south at midnight, setting in the west at dawn (l47-moon.png), and on about one night in six silver curtains of aurora
/// low in the north (l47-aurora.png); all made by tools/gen_47.py. They fade in as the fog lifts at dusk and out at dawn
/// (<see cref="AtmosphereSystem.L47Night"/>), and are added onto the sky (they glow, the fog does not touch them).
/// </summary>
public class L47Sky : ModSystem, IRenderer
{
    /// <summary>The moon's size (degrees across: the Moon looks half a degree; this one is "several times closer").</summary>
    private const double MoonAcross = 9;

    /// <summary>How far off things are drawn, as a share of the view distance: the stars, the aurora, the moon.</summary>
    private const float StarsAt = 0.8f, AuroraAt = 0.74f, MoonAt = 0.7f;

    private ICoreClientAPI capi;
    private WorldLayout layout;
    private MeshRef quad, dome;
    private int moonTex, starsTex, auroraTex;
    private readonly Matrixf model = new();

    public double RenderOrder => 0.43;
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
        var q = new MeshData(4, 6, false, true, true, true);
        q.AddVertex(-0.5f, -0.5f, 0, 0, 1, ColorUtil.WhiteArgb);
        q.AddVertex(0.5f, -0.5f, 0, 1, 1, ColorUtil.WhiteArgb);
        q.AddVertex(0.5f, 0.5f, 0, 1, 0, ColorUtil.WhiteArgb);
        q.AddVertex(-0.5f, 0.5f, 0, 0, 0, ColorUtil.WhiteArgb);
        q.AddIndices(0, 1, 2, 0, 2, 3);
        quad = capi.Render.UploadMesh(q);
        dome = capi.Render.UploadMesh(Sphere(24, 48));
        moonTex = capi.Render.GetOrLoadTexture(new AssetLocation("backrooms", "textures/environment/l47-moon.png"));
        starsTex = capi.Render.GetOrLoadTexture(new AssetLocation("backrooms", "textures/environment/l47-stars.png"));
        auroraTex = capi.Render.GetOrLoadTexture(new AssetLocation("backrooms", "textures/environment/l47-aurora.png"));
        capi.Event.RegisterRenderer(this, EnumRenderStage.Opaque, "backrooms-l47-sky");
    }

    /// <summary>A unit sphere seen from inside, its texture wrapped round it (longitude along u, latitude down v).</summary>
    private static MeshData Sphere(int rings, int segments)
    {
        var m = new MeshData((rings + 1) * (segments + 1), rings * segments * 6, false, true, true, true);
        for (int r = 0; r <= rings; r++)
        {
            double lat = Math.PI / 2 - r * Math.PI / rings;
            for (int s = 0; s <= segments; s++)
            {
                double lon = s * 2 * Math.PI / segments;
                m.AddVertex((float)(Math.Cos(lat) * Math.Cos(lon)), (float)Math.Sin(lat), (float)(Math.Cos(lat) * Math.Sin(lon)),
                    s / (float)segments, r / (float)rings, ColorUtil.WhiteArgb);
            }
        }
        for (int r = 0; r < rings; r++)
            for (int s = 0; s < segments; s++)
            {
                int a = r * (segments + 1) + s, b = a + segments + 1;
                m.AddIndices(new[] { a, a + 1, b });
                m.AddIndices(new[] { b, a + 1, b + 1 });
            }
        return m;
    }

    /// <summary>Player attribute (set by <c>/backrooms l47 aurora</c>, for the showcase): an aurora every night.</summary>
    public const string AuroraKey = "backrooms:l47Aurora";

    /// <summary>Whether there is an aurora on the night that began on a day (about one night in six, the same for everyone).</summary>
    public static bool AuroraOn(int worldSeed, double totalDays) =>
        Hashing.Unit(Hashing.Hash((ulong)(uint)worldSeed, (int)Math.Floor(totalDays + 0.25), 0, 0x30A0)) < 1 / 6.0;

    public void OnRenderFrame(float deltaTime, EnumRenderStage stage)
    {
        EntityPlayer player = capi.World.Player?.Entity;
        if (player == null || dome == null) return;
        int px = (int)Math.Floor(player.Pos.X), py = (int)Math.Floor(player.Pos.Y), pz = (int)Math.Floor(player.Pos.Z);
        if (layout.LevelAt(WorldLayout.MacroOf(px), WorldLayout.MacroOf(pz)) != WorldLayout.Level47) return;
        float night = AtmosphereSystem.L47Night(capi.World.Calendar);
        if (night < 0.02f) return;
        float view = Math.Max(64, capi.Settings.Int["viewDistance"]);
        IRenderAPI render = capi.Render;
        IStandardShaderProgram prog = render.PreparedStandardShader(px, py + 1, pz);
        prog.NormalShaded = 0;
        prog.DontWarpVertices = 1;
        prog.ExtraGlow = 255;
        prog.AlphaTest = 0.001f;
        prog.FogMinIn = 0;
        prog.FogDensityIn = 0;
        prog.RgbaAmbientIn = new Vec3f(1, 1, 1);
        prog.ViewMatrix = render.CameraMatrixOriginf;
        prog.ProjectionMatrix = render.CurrentProjectionMatrix;
        render.GlDisableCullFace();
        render.GLDepthMask(false);
        render.GlToggleBlend(true, EnumBlendMode.Glow);

        // The stars and the Milky Way, turning slowly with the night
        if (starsTex > 0)
        {
            float k = night * night;
            prog.Tex2D = starsTex;
            prog.RgbaLightIn = new Vec4f(k, k, k, 1);
            float d = StarsAt * view;
            double turn = capi.World.Calendar.TotalHours / 24.0 * Math.PI * 2 * 0.05;
            model.Identity().RotateY((float)turn).RotateX(0.35f).Scale(d, d, d);
            prog.ModelMatrix = model.Values;
            render.RenderMesh(dome);
        }

        // The aurora, low in the north, on its nights
        if (auroraTex > 0 && (AuroraOn(capi.World.Seed, capi.World.Calendar.TotalDays) || player.WatchedAttributes.GetBool(AuroraKey)))
        {
            double t = capi.World.ElapsedMilliseconds / 1000.0;
            float k = night * (0.55f + 0.25f * (float)Math.Sin(t * 0.21) + 0.2f * (float)Math.Sin(t * 0.53 + 1.3));
            prog.Tex2D = auroraTex;
            prog.RgbaLightIn = new Vec4f(k, k, k, 1);
            float d = AuroraAt * view;
            for (int c = 0; c < 3; c++)
            {
                double bearing = (-35 + c * 35 + 6 * Math.Sin(t * 0.05 + c)) * Math.PI / 180;
                Draw(prog, bearing, 22 * Math.PI / 180, d, d * 0.9f, d * 0.45f);
            }
        }

        // The moon: its far side, full, rising in the east at dusk and setting in the west at dawn
        if (moonTex > 0)
        {
            double hour = capi.World.Calendar.HourOfDay;
            double h = hour < 12 ? hour + 24 : hour;
            double f = Math.Clamp((h - 18.5) / 12.0, 0, 1);
            double bearing = (95 + 170 * f) * Math.PI / 180, elevation = (8 + 52 * Math.Sin(Math.PI * f)) * Math.PI / 180;
            float d = MoonAt * view, size = (float)(2 * d * Math.Tan(MoonAcross * Math.PI / 360));
            // (Over the stars: first a black disc so they do not shine through it, then the moon)
            render.GlToggleBlend(true, EnumBlendMode.Standard);
            prog.Tex2D = moonTex;
            prog.AlphaTest = 0.5f;
            if (night > 0.6f)
            {
                prog.RgbaLightIn = new Vec4f(0, 0, 0, 1);
                Draw(prog, bearing, elevation, d * 1.002f, size, size);
            }
            render.GlToggleBlend(true, EnumBlendMode.Glow);
            prog.AlphaTest = 0.001f;
            float k = Math.Min(1, night * 1.15f);
            prog.RgbaLightIn = new Vec4f(k, k * 0.98f, k * 0.94f, 1);
            Draw(prog, bearing, elevation, d, size, size);
        }

        render.GlToggleBlend(true, EnumBlendMode.Standard);
        render.GLDepthMask(true);
        render.GlEnableCullFace();
        prog.Stop();
    }

    /// <summary>A quad turned to face the eye at a bearing (radians clockwise from north) and height, a distance off, of a width and height.</summary>
    private void Draw(IStandardShaderProgram prog, double bearing, double elevation, float distance, float width, float height)
    {
        double dx = Math.Sin(bearing) * Math.Cos(elevation), dy = Math.Sin(elevation), dz = -Math.Cos(bearing) * Math.Cos(elevation);
        model.Identity().Translate((float)(dx * distance), (float)(dy * distance), (float)(dz * distance))
            .RotateY((float)Math.Atan2(-dx, -dz)).RotateX((float)elevation).Scale(width, height, 1);
        prog.ModelMatrix = model.Values;
        capi.Render.RenderMesh(quad);
    }

    public override void Dispose()
    {
        if (capi != null)
        {
            capi.Event.UnregisterRenderer(this, EnumRenderStage.Opaque);
            quad?.Dispose();
            dome?.Dispose();
        }
        base.Dispose();
    }
}
