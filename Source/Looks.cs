using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using Verse;

namespace IsoRim
{
    // One colour look for the 3D view.
    public class LookPreset
    {
        public string name;
        public string label;
        public string description;
        public float contrast;              // 0 to 1: deeper shadows and mid-tones
        public float desat;                 // 0 to 1: how much colour is taken out
        public float bright = 1f;           // scales the whole picture
        public Color lift = Color.black;    // a colour added to the shadows
        public Color gain = Color.white;    // a colour the highlights are multiplied by
        public float exposure;              // 0 to 0.5: brightens the whole picture

        public LookPreset(string name, string label, string description)
        {
            this.name = name;
            this.label = label;
            this.description = description;
        }
    }

    // The colour grade over the 3D view.
    //
    // Two ways of doing it:
    //   - Always available: a few see-through sheets held in front of the camera, each blended onto
    //     the picture in a different way (multiply, screen, a squaring curve, a pull toward grey).
    //     Together they shift the colour, lift or deepen the shadows and take colour out, using only
    //     the plain shader every Unity game has.
    //   - Exact: a colour lookup table (a LUT, a 1024 x 32 strip image of 32 slices) applied by a
    //     small shader. The shader has to be compiled in Unity, so it only works once the shader
    //     bundle has been built and put in the mod's Shaders folder (see the README). Every built-in
    //     look comes as a LUT file too, and any LUT file put in the LUTs folder can be picked.
    // The game's interface is drawn later and is not affected either way.
    [StaticConstructorOnStartup]
    public static class Looks
    {
        public const string CustomName = "Custom";
        private const float Pivot = 0.3f;   // the grey colours are pulled toward

        public static readonly List<LookPreset> Presets = new List<LookPreset>();

        static Looks()
        {
            Add("Gentle", "Gentle", "A little less colour and brightness. The mod's usual look.", desat: 0.15f, bright: 0.95f);
            Add("WarmAfternoon", "Warm afternoon", "Golden highlights and warm shadows.", desat: 0.06f, contrast: 0.2f,
                gain: new Color(1f, 0.95f, 0.85f), lift: new Color(0.03f, 0.015f, 0f));
            Add("CoolMorning", "Cool morning", "Fresh blue-green light, slightly muted.", desat: 0.12f,
                gain: new Color(0.90f, 0.96f, 1f), lift: new Color(0f, 0.012f, 0.035f));
            Add("Filmic", "Filmic", "Deeper shadows, softer colour and a faint warm cast, like film stock.", desat: 0.18f, contrast: 0.5f,
                gain: new Color(1f, 0.97f, 0.93f), lift: new Color(0.025f, 0.02f, 0.03f));
            Add("Bleak", "Bleak rim", "Washed-out, cold and hard: life on the edge.", desat: 0.45f, contrast: 0.25f, bright: 0.95f,
                gain: new Color(0.92f, 0.95f, 0.98f), lift: new Color(0.02f, 0.025f, 0.03f));
            Add("Vivid", "Vivid", "Punchier contrast and a touch brighter.", contrast: 0.45f, exposure: 0.06f);
            Add("Autumn", "Autumn", "Amber light and rich, earthy tones.", desat: 0.10f, contrast: 0.25f,
                gain: new Color(1f, 0.90f, 0.78f), lift: new Color(0.03f, 0.01f, 0f));
            Add("Moonlight", "Moonlight", "Cold blue night light over everything.", desat: 0.5f, bright: 0.9f,
                gain: new Color(0.72f, 0.82f, 1f), lift: new Color(0f, 0.01f, 0.04f));
            Add("Toxic", "Toxic", "A sickly green haze.", desat: 0.2f,
                gain: new Color(0.88f, 1f, 0.80f), lift: new Color(0.01f, 0.03f, 0f));
            Add("Sepia", "Sepia", "Old photograph browns.", desat: 0.85f,
                gain: new Color(1f, 0.88f, 0.70f), lift: new Color(0.04f, 0.025f, 0.01f));
            Add("Noir", "Noir", "Black and white with hard contrast.", desat: 1f, contrast: 0.6f);
            Presets.Add(new LookPreset(CustomName, "Custom", "Set colour and brightness yourself with the two sliders below."));
        }

        private static void Add(string name, string label, string description, float desat = 0f, float contrast = 0f, float bright = 1f,
            float exposure = 0f, Color? gain = null, Color? lift = null)
        {
            LookPreset p = new LookPreset(name, label, description);
            p.desat = desat;
            p.contrast = contrast;
            p.bright = bright;
            p.exposure = exposure;
            p.gain = gain ?? Color.white;
            p.lift = lift ?? Color.black;
            Presets.Add(p);
        }

        public static LookPreset Find(string name)
        {
            for (int i = 0; i < Presets.Count; i++)
            {
                if (Presets[i].name == name)
                {
                    return Presets[i];
                }
            }
            return Presets[0];
        }

        // The look in force, with the strength slider and the custom sliders worked in.
        public static LookPreset Current()
        {
            IsoRimSettings st = IsoRimMod.Settings;
            LookPreset p = Find(st.lookName);
            LookPreset r = new LookPreset(p.name, p.label, p.description);
            if (p.name == CustomName)
            {
                r.desat = 1f - Mathf.Clamp(st.saturation, 0.3f, 1f);
                r.bright = Mathf.Clamp(st.brightness, 0.3f, 1f);
                return r;
            }
            float k = Mathf.Clamp01(st.lookStrength);
            r.contrast = p.contrast * k;
            r.desat = p.desat * k;
            r.bright = Mathf.Lerp(1f, p.bright, k);
            r.exposure = p.exposure * k;
            r.gain = Color.Lerp(Color.white, p.gain, k);
            r.lift = Color.Lerp(Color.black, p.lift, k);
            return r;
        }

        // What a colour becomes under a look, worked out the same way the sheets do it. Used for the
        // previews in the options.
        public static Color Apply(LookPreset p, Color c)
        {
            float s, cc;
            ContrastTerms(p.contrast, out s, out cc);
            return new Color(Channel(p, c.r, 0, s, cc), Channel(p, c.g, 1, s, cc), Channel(p, c.b, 2, s, cc), 1f);
        }

        private static float Channel(LookPreset p, float x, int i, float s, float cc)
        {
            if (p.contrast > 0.001f)
            {
                float y = s * x;
                x = Mathf.Clamp01(y * (cc + y));
            }
            float keep = 1f - p.desat;
            x = Mathf.Clamp01(p.bright * (keep * x + (1f - keep) * Pivot));
            x = Mathf.Clamp01(x * p.gain[i]);
            x = Mathf.Clamp01(x + p.lift[i] * (1f - x));
            x = Mathf.Clamp01(x * (1f + p.exposure));
            return x;
        }

        // The squaring curve: x is first scaled by s, then multiplied by (cc + itself). s and cc are
        // picked so that white stays white and nothing overflows on the way.
        private static void ContrastTerms(float contrast, out float s, out float cc)
        {
            s = 1f - 0.25f * Mathf.Clamp01(contrast);
            cc = (1f - s * s) / s;
        }

        // ------------------------------------------------------------ drawing

        private const int Passes = 6;   // scale, curve, grey, gain, lift, exposure
        private static bool tried;
        private static Material[] passMats;
        private static Mesh[] passMeshes;
        private static readonly Vector3[] corners = new Vector3[4];
        private static readonly Color[] colours = new Color[4];

        // Called every frame while the 3D view is on.
        public static void Draw(Camera cam)
        {
            IsoRimSettings st = IsoRimMod.Settings;
            if (!st.grade || cam == null)
            {
                return;
            }
            View3D.ScreenCorners(2f, 1.1f, corners);
            if (st.useLut && Lut.Draw(cam, corners))
            {
                return;
            }
            if (!tried)
            {
                Init();
            }
            if (passMats == null)
            {
                return;
            }

            LookPreset p = Current();
            float s, cc;
            ContrastTerms(p.contrast, out s, out cc);
            if (p.contrast > 0.001f)
            {
                Sheet(cam, 0, new Color(s, s, s, 1f));
                Sheet(cam, 1, new Color(cc, cc, cc, 1f));
            }
            float keep = 1f - Mathf.Clamp01(p.desat);
            if (keep < 0.995f || p.bright < 0.995f)
            {
                float add = p.bright * (1f - keep) * Pivot;
                Sheet(cam, 2, new Color(add, add, add, p.bright * keep));
            }
            if (p.gain.r < 0.995f || p.gain.g < 0.995f || p.gain.b < 0.995f)
            {
                Sheet(cam, 3, new Color(p.gain.r, p.gain.g, p.gain.b, 1f));
            }
            if (p.lift.r > 0.002f || p.lift.g > 0.002f || p.lift.b > 0.002f)
            {
                Sheet(cam, 4, new Color(p.lift.r, p.lift.g, p.lift.b, 1f));
            }
            if (p.exposure > 0.002f)
            {
                Sheet(cam, 5, new Color(p.exposure, p.exposure, p.exposure, 1f));
            }
        }

        private static void Sheet(Camera cam, int pass, Color c)
        {
            Mesh mesh = passMeshes[pass];
            for (int i = 0; i < 4; i++)
            {
                colours[i] = c;
            }
            mesh.vertices = corners;
            mesh.colors = colours;
            mesh.RecalculateBounds();
            Graphics.DrawMesh(mesh, Matrix4x4.identity, passMats[pass], 0, cam);
        }

        private static void Init()
        {
            tried = true;
            try
            {
                Shader shader = Shader.Find("Hidden/Internal-Colored");
                if (shader == null)
                {
                    ModLog.Warn("[IsoRim] The colour grade needs a shader this game does not have, so it is off.");
                    return;
                }
                UnityEngine.Rendering.BlendMode[,] blends =
                {
                    { UnityEngine.Rendering.BlendMode.DstColor, UnityEngine.Rendering.BlendMode.Zero },          // out = src * dst
                    { UnityEngine.Rendering.BlendMode.DstColor, UnityEngine.Rendering.BlendMode.DstColor },      // out = dst * (src + dst)
                    { UnityEngine.Rendering.BlendMode.One, UnityEngine.Rendering.BlendMode.SrcAlpha },           // out = src + dst * alpha
                    { UnityEngine.Rendering.BlendMode.DstColor, UnityEngine.Rendering.BlendMode.Zero },          // out = src * dst
                    { UnityEngine.Rendering.BlendMode.OneMinusDstColor, UnityEngine.Rendering.BlendMode.One },   // screen
                    { UnityEngine.Rendering.BlendMode.DstColor, UnityEngine.Rendering.BlendMode.One },           // out = dst * (1 + src)
                };
                passMats = new Material[Passes];
                passMeshes = new Mesh[Passes];
                for (int i = 0; i < Passes; i++)
                {
                    Material m = new Material(shader);
                    m.name = "IsoRim_Look" + i;
                    m.SetInt("_SrcBlend", (int)blends[i, 0]);
                    m.SetInt("_DstBlend", (int)blends[i, 1]);
                    m.SetInt("_ZWrite", 0);
                    m.SetInt("_ZTest", (int)UnityEngine.Rendering.CompareFunction.Always);
                    m.SetInt("_Cull", (int)UnityEngine.Rendering.CullMode.Off);
                    m.renderQueue = 4900 + i;   // after everything else in the map view, in this order
                    passMats[i] = m;

                    Mesh mesh = new Mesh();
                    mesh.name = "IsoRim_Look" + i;
                    mesh.MarkDynamic();
                    mesh.vertices = corners;
                    mesh.colors = colours;
                    mesh.triangles = new int[] { 0, 1, 2, 0, 2, 3 };
                    passMeshes[i] = mesh;
                }
            }
            catch (Exception e)
            {
                passMats = null;
                Log.ErrorOnce("[IsoRim] Setting up the colour grade failed: " + e, 93611070);
            }
        }
    }

    // Exact colour grading with lookup tables, for when the shader bundle is present.
    [StaticConstructorOnStartup]
    public static class Lut
    {
        public const string BundleName = "isorimshaders";

        private static bool triedShader;
        private static Shader shader;
        private static Material material;
        private static Mesh mesh;
        private static readonly Dictionary<string, Texture2D> tables = new Dictionary<string, Texture2D>();
        private static List<string> files;
        private static string loadedFor;
        private static Texture2D current;
        private static int strengthId = -1;

        // True once the shader bundle has loaded.
        public static bool Available
        {
            get
            {
                LoadShader();
                return shader != null;
            }
        }

        public static string Folder
        {
            get { return IsoRimMod.RootDir != null ? Path.Combine(IsoRimMod.RootDir, "LUTs") : null; }
        }

        // The names (without .png) of the LUT files in the LUTs folder.
        public static List<string> Files
        {
            get
            {
                if (files == null)
                {
                    files = new List<string>();
                    try
                    {
                        string dir = Folder;
                        if (dir != null && Directory.Exists(dir))
                        {
                            foreach (string f in Directory.GetFiles(dir, "*.png"))
                            {
                                files.Add(Path.GetFileNameWithoutExtension(f));
                            }
                            files.Sort();
                        }
                    }
                    catch (Exception e)
                    {
                        ModLog.Warn("[IsoRim] Could not list the LUT files: " + e.Message);
                    }
                }
                return files;
            }
        }

        public static void Rescan()
        {
            files = null;
        }

        private static void LoadShader()
        {
            if (triedShader)
            {
                return;
            }
            triedShader = true;
            try
            {
                if (IsoRimMod.RootDir == null)
                {
                    return;
                }
                string suffix = "";
                if (Application.platform == RuntimePlatform.OSXPlayer || Application.platform == RuntimePlatform.OSXEditor)
                {
                    suffix = "_mac";
                }
                else if (Application.platform == RuntimePlatform.LinuxPlayer || Application.platform == RuntimePlatform.LinuxEditor)
                {
                    suffix = "_linux";
                }
                string path = Path.Combine(Path.Combine(IsoRimMod.RootDir, "Shaders"), BundleName + suffix);
                if (!File.Exists(path))
                {
                    path = Path.Combine(Path.Combine(IsoRimMod.RootDir, "Shaders"), BundleName);
                }
                if (!File.Exists(path))
                {
                    return;   // not built yet: the sheet grade is used instead
                }
                AssetBundle bundle = AssetBundle.LoadFromFile(path);
                if (bundle == null)
                {
                    ModLog.Warn("[IsoRim] The shader bundle " + path + " could not be loaded. It may have been built for another platform or Unity version.");
                    return;
                }
                foreach (Shader s in bundle.LoadAllAssets<Shader>())
                {
                    if (s != null && s.name == "IsoRim/LUT")
                    {
                        shader = s;
                    }
                }
                if (shader == null || !shader.isSupported)
                {
                    ModLog.Warn("[IsoRim] The shader bundle has no usable IsoRim/LUT shader.");
                    shader = null;
                    return;
                }
                ModLog.Debug("[IsoRim] Exact colour grading (LUT) is available.");
            }
            catch (Exception e)
            {
                shader = null;
                ModLog.Warn("[IsoRim] Loading the shader bundle failed: " + e.Message);
            }
        }

        // The table for the chosen look: a LUT file named after the look, or the chosen LUT file.
        private static Texture2D TableFor(string name)
        {
            Texture2D tex;
            if (tables.TryGetValue(name, out tex))
            {
                return tex;
            }
            tex = null;
            try
            {
                string path = Folder != null ? Path.Combine(Folder, name + ".png") : null;
                if (path != null && File.Exists(path))
                {
                    tex = new Texture2D(2, 2, TextureFormat.RGBA32, false, false);
                    if (ImageConversion.LoadImage(tex, File.ReadAllBytes(path), false) && tex.width == tex.height * tex.height)
                    {
                        tex.filterMode = FilterMode.Bilinear;
                        tex.wrapMode = TextureWrapMode.Clamp;
                        tex.anisoLevel = 0;
                    }
                    else
                    {
                        ModLog.Warn("[IsoRim] " + path + " is not a LUT strip (it must be N*N wide and N high, for example 1024 x 32).");
                        UnityEngine.Object.Destroy(tex);
                        tex = null;
                    }
                }
            }
            catch (Exception e)
            {
                ModLog.Warn("[IsoRim] Could not read LUT " + name + ": " + e.Message);
                tex = null;
            }
            tables[name] = tex;
            return tex;
        }

        // Draws the grade with a LUT. Returns false if it cannot, so the sheets are used instead.
        public static bool Draw(Camera cam, Vector3[] corners)
        {
            IsoRimSettings st = IsoRimMod.Settings;
            string name = st.lutFile.NullOrEmpty() ? st.lookName : st.lutFile;
            if (name == Looks.CustomName || !Available)
            {
                return false;
            }
            if (loadedFor != name)
            {
                loadedFor = name;
                current = TableFor(name);
            }
            if (current == null)
            {
                return false;
            }
            if (material == null)
            {
                material = new Material(shader);
                material.name = "IsoRim_LUT";
                material.renderQueue = 4950;
                strengthId = Shader.PropertyToID("_Strength");
                mesh = new Mesh();
                mesh.name = "IsoRim_LUT";
                mesh.MarkDynamic();
                mesh.vertices = corners;
                mesh.triangles = new int[] { 0, 1, 2, 0, 2, 3 };
            }
            material.mainTexture = current;
            material.SetTexture("_LutTex", current);
            material.SetFloat(strengthId, Mathf.Clamp01(st.lookStrength));
            mesh.vertices = corners;
            mesh.RecalculateBounds();
            Graphics.DrawMesh(mesh, Matrix4x4.identity, material, 0, cam);
            return true;
        }
    }
}
