using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using HarmonyLib;
using RimWorld;
using UnityEngine;
using Verse;

namespace IsoRim
{
    // Repeatable "random" numbers from map coordinates or a thing's id, so that a given rock
    // corner or tree looks the same every time the map is redrawn.
    public static class Hashing
    {
        // A value from 0 to 1.
        public static float Unit(int a, int b, int salt)
        {
            unchecked
            {
                int h = (a * 73856093) ^ (b * 19349663) ^ (salt * 83492791);
                h = (h ^ (int)((uint)h >> 13)) * 1274126177;
                h ^= (int)((uint)h >> 16);
                return (h & 0xFFFF) / 65535f;
            }
        }
    }

    // Draws a model every frame, for things that move: a weapon in a colonist's hands, the two
    // leaves of a door. (Everything that stays put is written into the map mesh by ModelBaker
    // instead, which costs nothing per frame.) The model is turned into a few ready-made meshes
    // the first time it is needed in a given colour and kept.
    public static class DynamicModels
    {
        public class Part
        {
            public Mesh mesh;
            public Material material;
            public bool outline;
        }

        private class Lists
        {
            public List<Vector3> verts = new List<Vector3>();
            public List<Color32> colors = new List<Color32>();
            public List<Vector2> uvs = new List<Vector2>();
            public List<int> tris = new List<int>();
            public Material material;

            public void Add(Vector3 v, Color32 c, Vector2 uv)
            {
                tris.Add(verts.Count);
                verts.Add(v);
                colors.Add(c);
                uvs.Add(uv);
            }

            public Mesh ToMesh()
            {
                Mesh mesh = new Mesh();
                mesh.SetVertices(verts);
                mesh.SetColors(colors);
                mesh.SetUVs(0, uvs);
                mesh.SetTriangles(tris, 0);
                mesh.RecalculateBounds();
                return mesh;
            }
        }

        private static readonly Dictionary<long, List<Part>> cache = new Dictionary<long, List<Part>>();
        private static int builtForLight = -1;
        private static readonly Color32 White = new Color32(255, 255, 255, 255);

        // Meshes no longer wanted are destroyed a couple of frames later rather than at once:
        // one may already be queued to draw this frame, and destroying it would make whatever
        // it shows blink out for that frame.
        private static readonly List<Mesh> retired = new List<Mesh>();
        private static readonly List<int> retiredAt = new List<int>();

        public static void Retire(Mesh mesh)
        {
            if (mesh == null)
            {
                return;
            }
            retired.Add(mesh);
            retiredAt.Add(Time.frameCount);
        }

        private static void Sweep()
        {
            int now = Time.frameCount;
            int done = 0;
            while (done < retired.Count && now - retiredAt[done] > 2)
            {
                if (retired[done] != null)
                {
                    UnityEngine.Object.Destroy(retired[done]);
                }
                done++;
            }
            if (done > 0)
            {
                retired.RemoveRange(0, done);
                retiredAt.RemoveRange(0, done);
            }
        }

        // Throws away every ready-made mesh; they are made again as they are needed.
        public static void Forget()
        {
            foreach (KeyValuePair<long, List<Part>> pair in cache)
            {
                List<Part> parts = pair.Value;
                for (int i = 0; i < parts.Count; i++)
                {
                    if (parts[i].mesh != null)
                    {
                        Retire(parts[i].mesh);
                    }
                }
            }
            cache.Clear();
        }

        // position: x and z in map cells, y the height above the ground in cells.
        // yaw: turn about the vertical axis in degrees. swatch: Wood, Stone, Metal or Fabric.
        public static void Draw(Model m, Vector3 position, float yaw, Vector3 scale, Color tint, string swatch)
        {
            if (m == null)
            {
                return;
            }
            List<Part> parts = PartsFor(m, tint, swatch, 0);
            if (parts.Count == 0)
            {
                return;
            }

            // The whole map is drawn squashed flat (see View3D); dividing height by the same
            // factor here makes the model come out its true shape.
            float s = View3D.Squash;
            Matrix4x4 matrix = Matrix4x4.Translate(new Vector3(position.x, position.y / s, position.z))
                * Matrix4x4.Scale(new Vector3(1f, 1f / s, 1f))
                * Matrix4x4.TRS(Vector3.zero, Quaternion.AngleAxis(yaw, Vector3.up), scale);
            Submit(parts, matrix);
        }

        // Draws ready-made parts (from BuildMerged) the same way DrawLocal places a model.
        public static void DrawParts(List<Part> parts, Vector3 position, float yaw, Matrix4x4 local)
        {
            if (parts == null || parts.Count == 0)
            {
                return;
            }
            float s = View3D.Squash;
            Matrix4x4 matrix = Matrix4x4.Translate(new Vector3(position.x, position.y / s, position.z))
                * Matrix4x4.Scale(new Vector3(1f, 1f / s, 1f))
                * Matrix4x4.Rotate(Quaternion.AngleAxis(yaw, Vector3.up))
                * local;
            Submit(parts, matrix);
        }

        public static void Destroy(List<Part> parts)
        {
            if (parts == null)
            {
                return;
            }
            for (int i = 0; i < parts.Count; i++)
            {
                if (parts[i].mesh != null)
                {
                    Retire(parts[i].mesh);
                }
            }
            parts.Clear();
        }

        // Several plain-coloured models, each with its own placing and colour, put together into
        // one solid mesh and one outline mesh: one draw each instead of one per model. Shaded for
        // a whole turned the given number of eighths from north. Textures are left off.
        public static List<Part> BuildMerged(List<Model> models, List<Matrix4x4> locals, List<Color> tints, int turned)
        {
            List<Part> parts = new List<Part>();
            Material solidMat = R3DMaterials.Solid;
            if (solidMat == null)
            {
                return parts;
            }
            Quaternion facing = Quaternion.AngleAxis(turned * 45f, Vector3.up);
            Lists solid = new Lists();
            Lists outline = new Lists();
            try
            {
                for (int k = 0; k < models.Count; k++)
                {
                    Model m = models[k];
                    Matrix4x4 local = locals[k];
                    Color tint = tints[k];
                    int n = m.positions.Length;
                    for (int i = 0; i + 2 < n; i += 3)
                    {
                        int mi = m.material != null ? m.material[i] : 0;
                        ModelMaterial mm = m.materials != null ? m.materials[mi] : null;
                        Vector3 normal = facing * local.MultiplyVector(m.normals[i]).normalized;
                        float shade = mm != null && mm.glow ? 1f : R3DMaterials.Shade(normal);
                        for (int v = i; v < i + 3; v++)
                        {
                            Color c = m.colors[v];
                            if (m.tinted[v])
                            {
                                c *= tint;
                            }
                            solid.Add(local.MultiplyPoint3x4(m.positions[v]), R3DMaterials.Shaded(c, shade), Vector2.zero);
                            if (m.hull != null)
                            {
                                outline.Add(local.MultiplyPoint3x4(m.positions[v] + m.hull[v]), R3DMaterials.Shaded(c, ModelBaker.OutlineShade), Vector2.zero);
                            }
                        }
                    }
                }
                if (solid.verts.Count > 0)
                {
                    Part p = new Part();
                    p.mesh = solid.ToMesh();
                    p.material = solidMat;
                    parts.Add(p);
                }
                Material outlineMat = R3DMaterials.Outline;
                if (outline.verts.Count > 0 && outlineMat != null)
                {
                    Part p = new Part();
                    p.mesh = outline.ToMesh();
                    p.material = outlineMat;
                    p.outline = true;
                    parts.Add(p);
                }
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Putting a figure together failed: " + e, 93611031);
            }
            return parts;
        }

        // The same for one part of something that moves as a whole, such as an animal's body
        // or one of its legs. local places the part within the whole, in cells, before the whole
        // is turned by yaw and put at position. The light stays where it is as the whole turns:
        // the shading is worked out again for each eighth of a turn.
        public static void DrawLocal(Model m, Vector3 position, float yaw, Matrix4x4 local, Color tint, string swatch)
        {
            if (m == null)
            {
                return;
            }
            int turned = Mathf.RoundToInt(Mathf.Repeat(yaw, 360f) / 45f) % 8;
            List<Part> parts = PartsFor(m, tint, swatch, turned);
            if (parts.Count == 0)
            {
                return;
            }
            float s = View3D.Squash;
            Matrix4x4 matrix = Matrix4x4.Translate(new Vector3(position.x, position.y / s, position.z))
                * Matrix4x4.Scale(new Vector3(1f, 1f / s, 1f))
                * Matrix4x4.Rotate(Quaternion.AngleAxis(yaw, Vector3.up))
                * local;
            Submit(parts, matrix);
        }

        private static void Submit(List<Part> parts, Matrix4x4 matrix)
        {
            if (retired.Count > 0)
            {
                Sweep();
            }
            bool outlines = IsoRimMod.Settings.outlines;
            for (int i = 0; i < parts.Count; i++)
            {
                Part p = parts[i];
                if (p.outline && !outlines)
                {
                    continue;
                }
                Graphics.DrawMesh(p.mesh, matrix, p.material, 0);
            }
        }

        // turned: how many eighths of a turn the model is facing away from north, for the shading.
        private static List<Part> PartsFor(Model m, Color tint, string swatch, int turned)
        {
            bool textured = IsoRimMod.Settings.texturedModels && m.materials != null && m.uvs != null && m.material != null;

            // Colours are rounded a little, so that people's clothes and drifting smoke, which
            // come in endless shades, share ready-made meshes instead of each needing its own.
            Color32 t = tint;
            t.r = (byte)(t.r & 0xF8);
            t.g = (byte)(t.g & 0xF8);
            t.b = (byte)(t.b & 0xF8);
            t.a = 255;
            tint = t;
            // Meshes shaded for an old light direction are of no further use once the camera has turned.
            if (cache.Count > 6000 || builtForLight != R3DMaterials.LightStep)
            {
                Forget();
                builtForLight = R3DMaterials.LightStep;
            }
            long key = ((long)m.id << 34) | ((long)R3DMaterials.LightStep << 31) | ((long)turned << 28) | ((long)(textured ? 1 : 0) << 27) | ((long)R3DTextures.SwatchIndex(swatch) << 24)
                | (uint)((t.r << 16) | (t.g << 8) | t.b);

            List<Part> parts;
            if (cache.TryGetValue(key, out parts))
            {
                return parts;
            }
            parts = new List<Part>();
            cache[key] = parts;
            try
            {
                Build(m, tint, swatch, textured, parts, turned);
            }
            catch (Exception e)
            {
                parts.Clear();
                Log.ErrorOnce("[IsoRim] Preparing a model for drawing failed: " + e, 93611030);
            }
            return parts;
        }

        // The same three layers ModelBaker writes: a plain solid copy, an enlarged inside-out
        // copy for the outline, and the textured faces.
        private static void Build(Model m, Color tint, string swatch, bool textured, List<Part> parts, int turned)
        {
            Quaternion facing = Quaternion.AngleAxis(turned * 45f, Vector3.up);
            Material solidMat = R3DMaterials.Solid;
            if (solidMat == null)
            {
                return;
            }
            Lists solid = new Lists();
            Lists outline = new Lists();
            Lists[] texturedLists = textured ? new Lists[m.materials.Length * ModelBaker.Levels.Length] : null;
            bool[] looked = textured ? new bool[m.materials.Length * ModelBaker.Levels.Length] : null;

            int n = m.positions.Length;
            for (int i = 0; i + 2 < n; i += 3)
            {
                float shade = R3DMaterials.Shade(turned == 0 ? m.normals[i] : facing * m.normals[i]);
                int mi = m.material != null ? m.material[i] : 0;
                ModelMaterial mm = m.materials != null ? m.materials[mi] : null;
                if (mm != null && mm.glow)
                {
                    shade = 1f;   // a flame is as bright on every side
                }

                Lists tl = null;
                if (textured && mm != null && mm.texture != null)
                {
                    int level = ModelBaker.LevelOf(shade);
                    int slot = mi * ModelBaker.Levels.Length + level;
                    if (!looked[slot])
                    {
                        looked[slot] = true;
                        Color c = mm.color * ModelBaker.Levels[level];
                        if (mm.tinted)
                        {
                            c *= tint;
                        }
                        Material tmat = R3DTextures.MaterialFor(mm.texture.Replace("{stuff}", swatch), c);
                        if (tmat != null)
                        {
                            texturedLists[slot] = new Lists();
                            texturedLists[slot].material = tmat;
                        }
                    }
                    tl = texturedLists[slot];
                }

                for (int k = i; k < i + 3; k++)
                {
                    Vector3 hull = m.hull != null ? m.hull[k] : Vector3.zero;
                    Color c = m.colors[k];
                    if (m.tinted[k])
                    {
                        c *= tint;
                    }
                    solid.Add(tl != null ? m.positions[k] - hull * ModelBaker.Inset : m.positions[k], R3DMaterials.Shaded(c, shade), Vector2.zero);
                    if (m.hull != null)
                    {
                        outline.Add(m.positions[k] + hull, R3DMaterials.Shaded(c, ModelBaker.OutlineShade), Vector2.zero);
                    }
                    if (tl != null)
                    {
                        tl.Add(m.positions[k] + m.normals[i] * ModelBaker.FaceLift, White, m.uvs[k]);
                    }
                }
            }

            if (solid.verts.Count > 0)
            {
                Part p = new Part();
                p.mesh = solid.ToMesh();
                p.material = solidMat;
                parts.Add(p);
            }
            Material outlineMat = R3DMaterials.Outline;
            if (outline.verts.Count > 0 && outlineMat != null)
            {
                Part p = new Part();
                p.mesh = outline.ToMesh();
                p.material = outlineMat;
                p.outline = true;
                parts.Add(p);
            }
            if (texturedLists != null)
            {
                for (int i = 0; i < texturedLists.Length; i++)
                {
                    Lists l = texturedLists[i];
                    if (l == null || l.verts.Count == 0)
                    {
                        continue;
                    }
                    Part p = new Part();
                    p.mesh = l.ToMesh();
                    p.material = l.material;
                    parts.Add(p);
                }
            }
        }
    }

    // Swaps the game's ground textures for the mod's own while the 3D view is on, and puts the
    // originals back when it is off. Only the picture changes: the game goes on drawing the
    // ground, blending edges and tinting stone as before.
    //   - natural ground (soil, sand, gravel, stone ...), with soil optionally drawn as grass;
    //   - built floors (wood, stone tile, flagstone, carpet, concrete, metal ...);
    // (Water is drawn by the mod's own layer; see SectionLayer_IsoRimWater.)
    public static class Ground
    {
        private struct Saved
        {
            public Texture texture;
            public Color color;
        }

        private static int applied;   // which of the options below are in force; 0 = the game's own textures
        private static readonly Dictionary<Material, Saved> originals = new Dictionary<Material, Saved>();

        // Called every frame; does nothing unless the wanted state has changed.
        public static void Sync()
        {
            IsoRimSettings st = IsoRimMod.Settings;
            int want = 0;
            if (View3D.Active)
            {
                want = (st.groundStyle ? 1 : 0) | (st.groundStyle && st.grassSoil ? 2 : 0) | (st.floorStyle ? 4 : 0);
            }
            if (want == applied)
            {
                return;
            }
            applied = want;
            try
            {
                Restore();
                if (want != 0)
                {
                    Apply(st);
                }
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Changing the ground textures failed: " + e, 93611050);
            }
        }

        private static void Apply(IsoRimSettings st)
        {
            int changed = 0;
            foreach (TerrainDef def in DefDatabase<TerrainDef>.AllDefsListForReading)
            {
                Material mat = def.DrawMatSingle;
                if (mat == null || !mat.HasProperty("_MainTex"))
                {
                    continue;
                }

                if (IsWater(def))
                {
                    continue;
                }

                Color tint = Color.white;
                bool ownTint = false;
                string kind = st.floorStyle ? FloorKind(def, ref tint, ref ownTint) : null;
                if (kind == null && st.groundStyle)
                {
                    kind = KindOf(def);
                    if (st.grassSoil)
                    {
                        // Bare earth is drawn as turf. Rich soil gets a darker, lusher turf so that
                        // the good farmland can still be told apart at a glance.
                        if (kind == "Soil")
                        {
                            kind = "Grass";
                        }
                        else if (kind == "SoilRich")
                        {
                            kind = "GrassRich";
                        }
                    }
                }
                if (kind == null)
                {
                    continue;
                }
                Texture2D tex = R3DTextures.Get("IsoRim/Ground/" + kind);
                if (tex == null)
                {
                    continue;
                }
                Remember(mat);
                mat.mainTexture = tex;

                // The floor pictures are plain grey. Where the game tints the floor itself (stone,
                // carpet) that is all that is needed; where its own picture carried the colour,
                // the colour is supplied here.
                if (ownTint && mat.HasProperty("_Color"))
                {
                    Color c = mat.color;
                    if (c.r > 0.93f && c.g > 0.93f && c.b > 0.93f)
                    {
                        mat.color = new Color(tint.r, tint.g, tint.b, c.a);
                    }
                }
                changed++;
            }
            if (changed == 0)
            {
                ModLog.Warn("[IsoRim] No ground textures could be replaced.");
            }
        }

        private static void Remember(Material mat)
        {
            if (originals.ContainsKey(mat))
            {
                return;
            }
            Saved saved = new Saved();
            saved.texture = mat.mainTexture;
            saved.color = mat.HasProperty("_Color") ? mat.color : Color.white;
            originals[mat] = saved;
        }

        private static void Restore()
        {
            foreach (KeyValuePair<Material, Saved> pair in originals)
            {
                Material mat = pair.Key;
                if (mat == null)
                {
                    continue;
                }
                mat.mainTexture = pair.Value.texture;
                if (mat.HasProperty("_Color"))
                {
                    mat.color = pair.Value.color;
                }
            }
        }

        // Open water. Marshy ground is not: it keeps the mod's own marsh picture.
        public static bool IsWater(TerrainDef def)
        {
            if (def == null)
            {
                return false;
            }
            string name = def.defName ?? "";
            if (Has(name, "Marsh"))
            {
                return false;
            }
            return (def.tags != null && def.tags.Contains("Water")) || Has(name, "Water");
        }

        private static readonly Color WoodTint = new Color(0.60f, 0.44f, 0.30f);
        private static readonly Color ConcreteTint = new Color(0.62f, 0.62f, 0.60f);
        private static readonly Color PavedTint = new Color(0.56f, 0.53f, 0.50f);
        private static readonly Color SteelTint = new Color(0.47f, 0.49f, 0.53f);
        private static readonly Color SilverTint = new Color(0.80f, 0.82f, 0.84f);
        private static readonly Color GoldTint = new Color(0.88f, 0.72f, 0.30f);
        private static readonly Color SterileTint = new Color(0.90f, 0.92f, 0.92f);

        // Which of the mod's floor textures suits a built floor, or null to leave it alone.
        // tint is the colour to give it if the game does not tint that floor itself.
        private static string FloorKind(TerrainDef def, ref Color tint, ref bool ownTint)
        {
            string name = def.defName ?? "";
            string both = name + " " + (def.texturePath ?? "");
            if (Has(both, "Burned") || Has(both, "Water"))
            {
                return null;
            }
            if (Has(both, "WoodPlank") || Has(both, "WoodFloor") || Has(name, "Bridge"))
            {
                tint = WoodTint;
                ownTint = true;
                return "FloorWood";
            }
            if (Has(both, "Flagstone"))
            {
                return "FloorFlagstone";
            }
            if (Has(both, "Carpet"))
            {
                return "FloorCarpet";
            }
            if (Has(both, "Sterile"))
            {
                tint = SterileTint;
                ownTint = true;
                return "FloorSterile";
            }
            if (Has(name, "SilverTile") || Has(name, "GoldTile") || Has(name, "MetalTile"))
            {
                tint = Has(name, "Silver") ? SilverTint : (Has(name, "Gold") ? GoldTint : SteelTint);
                ownTint = true;
                return "FloorMetal";
            }
            if (Has(both, "PavedTile"))
            {
                tint = PavedTint;
                ownTint = true;
                return "FloorPaved";
            }
            if (Has(both, "Concrete"))
            {
                tint = ConcreteTint;
                ownTint = true;
                return "FloorConcrete";
            }
            if (Has(both, "TilesStone") || Has(both, "StoneTile") || (name.StartsWith("Tile") && def.layerable))
            {
                return "FloorStoneTile";
            }
            return null;
        }

        // Which of the mod's ground textures suits a natural terrain, or null to leave it alone.
        private static string KindOf(TerrainDef def)
        {
            string name = def.defName ?? "";
            string both = name + " " + (def.texturePath ?? "");
            if (def.layerable)
            {
                return null;   // a built floor the mod has no texture for
            }
            if (Has(both, "Water") || Has(both, "Bridge") || Has(both, "Floor") || Has(both, "Tile") || Has(both, "Flagstone")
                || Has(both, "Carpet") || Has(both, "Concrete") || Has(both, "Paved") || Has(both, "Burned") || Has(both, "Asphalt"))
            {
                return null;
            }

            // Stone ground is generated once per kind of rock, named like Granite_Rough.
            if (name.EndsWith("_RoughHewn"))
            {
                return "RoughHewn";
            }
            if (name.EndsWith("_Rough"))
            {
                return "RoughStone";
            }
            if (name.EndsWith("_Smooth"))
            {
                return "SmoothStone";
            }

            if (Has(both, "SoilRich") || Has(both, "RichSoil"))
            {
                return "SoilRich";
            }
            if (Has(both, "Marsh"))
            {
                return "Marsh";
            }
            if (Has(both, "Moss"))
            {
                return "Moss";
            }
            if (Has(both, "Mud"))
            {
                return "Mud";
            }
            if (Has(both, "PackedDirt"))
            {
                return "PackedDirt";
            }
            if (Has(both, "Gravel"))
            {
                return "Gravel";
            }
            if (Has(both, "Sand"))
            {
                return "Sand";
            }
            if (name == "Ice")
            {
                return "Ice";
            }
            if (Has(both, "Soil"))
            {
                return "Soil";
            }
            return null;
        }

        private static bool Has(string text, string word)
        {
            return text.IndexOf(word, StringComparison.OrdinalIgnoreCase) >= 0;
        }
    }

    // Decides which walls are cut down to show what is behind them (the stretch under the
    // pointer, and optionally the walls in front of roofed rooms) and redraws the parts of the
    // map they are in when that changes, because the game only redraws walls when the walls
    // themselves change.
    public static class Cutaway
    {
        private struct Pending
        {
            public Map map;
            public int sx;
            public int sz;
            public float due;
        }

        private const int SectionSize = 17;   // the game's map mesh is built in 17 x 17 blocks

        private static readonly List<Pending> queue = new List<Pending>();
        private static bool looked;
        private static MethodInfo sectionAt;
        private static MethodInfo regenerate;
        private static MethodInfo getLayer;
        private static MethodInfo regenerateLayer;
        private static Type thingsLayer;

        // ---- what is dissolved round the pointer and the colonists ------------------------------
        // Walls within reach of the pointer (and, as an option, of each colonist) are lowered,
        // trees there lose their leaves so what is under them shows, and the roof of the room
        // under the pointer (or of rooms with colonists in them) is lifted off. All of these are
        // part of the map's ready-made mesh, so the blocks they are in are redrawn when the sets
        // change, after the pointer has settled for a moment.

        private static HashSet<IntVec3> cutWalls = new HashSet<IntVec3>();
        private static HashSet<IntVec3> thinTrees = new HashSet<IntVec3>();
        private static HashSet<IntVec3> openRoofs = new HashSet<IntVec3>();
        private static HashSet<IntVec3> wantWalls = new HashSet<IntVec3>();
        private static HashSet<IntVec3> wantTrees = new HashSet<IntVec3>();
        private static HashSet<IntVec3> wantRoofs = new HashSet<IntVec3>();
        private static readonly List<IntVec3> redraw = new List<IntVec3>();
        private static readonly List<IntVec3> redrawRoofs = new List<IntVec3>();
        private static readonly List<IntVec3> redrawTrees = new List<IntVec3>();
        private static readonly List<Vector3> pointerFoci = new List<Vector3>();
        private static readonly List<Vector3> colonistFoci = new List<Vector3>();
        private static readonly HashSet<Room> rooms = new HashSet<Room>();
        private static Map hoverMap;
        private static int appliedSig;
        private static int wantedSig;
        private static float wantedSince;
        private static int lastScan = -1000;

        public static bool Hovered(Map map, IntVec3 c)
        {
            return map == hoverMap && cutWalls.Count > 0 && cutWalls.Contains(c);
        }

        public static bool TreeThinned(Map map, IntVec3 c)
        {
            return map == hoverMap && thinTrees.Count > 0 && thinTrees.Contains(c);
        }

        public static bool RoofOpen(Map map, IntVec3 c)
        {
            return map == hoverMap && openRoofs.Count > 0 && openRoofs.Contains(c);
        }

        // Called every frame while the 3D view is on.
        public static void TrackPointer()
        {
            Map map = Find.CurrentMap;
            if (map != hoverMap)
            {
                cutWalls.Clear();
                thinTrees.Clear();
                openRoofs.Clear();
                hoverMap = map;
                appliedSig = 0;
                wantedSig = 0;
            }
            if (map == null)
            {
                return;
            }
            int frame = Time.frameCount;
            if (frame - lastScan >= 4)
            {
                lastScan = frame;
                try
                {
                    Gather(map);
                }
                catch (Exception e)
                {
                    Log.ErrorOnce("[IsoRim] Working out what to see through failed: " + e, 93611072);
                    return;
                }
            }
            int sig = Signature(wantWalls, 1) ^ Signature(wantTrees, 2) ^ Signature(wantRoofs, 3);
            if (sig == appliedSig)
            {
                wantedSig = sig;
                return;
            }
            if (sig != wantedSig)
            {
                wantedSig = sig;
                wantedSince = Time.realtimeSinceStartup;
                return;
            }
            // Wait for the pointer to settle, a little longer before putting things back.
            bool growing = wantWalls.Count + wantTrees.Count + wantRoofs.Count >= cutWalls.Count + thinTrees.Count + openRoofs.Count;
            if (Time.realtimeSinceStartup - wantedSince < (growing ? 0.08f : 0.25f))
            {
                return;
            }

            redraw.Clear();
            redrawTrees.Clear();
            redrawRoofs.Clear();
            NoteChanges(cutWalls, wantWalls, redraw, 1);
            NoteChanges(thinTrees, wantTrees, redrawTrees, 0);
            NoteChanges(openRoofs, wantRoofs, redrawRoofs, SectionLayer_IsoRimRoofs.Reach);
            Swap(ref cutWalls, ref wantWalls);
            Swap(ref thinTrees, ref wantTrees);
            Swap(ref openRoofs, ref wantRoofs);
            appliedSig = sig;
            for (int i = 0; i < redraw.Count; i++)
            {
                RedrawWalls(map, redraw[i]);
            }
            for (int i = 0; i < redrawTrees.Count; i++)
            {
                RedrawLayer(map, redrawTrees[i], typeof(SectionLayer_IsoRimTrees));
            }
            for (int i = 0; i < redrawRoofs.Count; i++)
            {
                RedrawLayer(map, redrawRoofs[i], typeof(SectionLayer_IsoRimRoofs));
            }
            // The swapped-out sets now hold the old state; they are refilled on the next look.
        }

        private static void Swap(ref HashSet<IntVec3> a, ref HashSet<IntVec3> b)
        {
            HashSet<IntVec3> t = a;
            a = b;
            b = t;
        }

        private static int Signature(HashSet<IntVec3> cells, int salt)
        {
            unchecked
            {
                int h = cells.Count * 7919 * salt;
                foreach (IntVec3 c in cells)
                {
                    h += (c.x * 73856093) ^ (c.z * 19349663) ^ (salt * 83492791);
                }
                return h;
            }
        }

        // Notes the blocks holding every cell that changes; with neighbours, the blocks of the
        // cells beside it too (a wall next to a lowered one shows a side it did not show before).
        private static void NoteChanges(HashSet<IntVec3> now, HashSet<IntVec3> next, List<IntVec3> into, int neighbours)
        {
            foreach (IntVec3 c in now)
            {
                if (!next.Contains(c))
                {
                    NoteBlock(c, into, neighbours);
                }
            }
            foreach (IntVec3 c in next)
            {
                if (!now.Contains(c))
                {
                    NoteBlock(c, into, neighbours);
                }
            }
        }

        // reach: how many cells round the changed one can look different because of it. A block
        // is 17 cells across, so checking the corners and edge middles of that square finds them all.
        private static void NoteBlock(IntVec3 c, List<IntVec3> into, int reach)
        {
            NoteOne(c.x, c.z, into);
            if (reach <= 0)
            {
                return;
            }
            for (int dx = -reach; dx <= reach; dx += reach)
            {
                for (int dz = -reach; dz <= reach; dz += reach)
                {
                    NoteOne(c.x + dx, c.z + dz, into);
                }
            }
        }

        private static void NoteOne(int x, int z, List<IntVec3> into)
        {
            if (x < 0 || z < 0)
            {
                return;
            }
            IntVec3 corner = new IntVec3(x / SectionSize * SectionSize + 1, 0, z / SectionSize * SectionSize + 1);
            if (!into.Contains(corner))
            {
                into.Add(corner);
            }
        }

        private static bool PointerOnInterface()
        {
            return Find.WindowStack != null && Find.WindowStack.GetWindowAt(Verse.UI.MousePositionOnUIInverted) != null;
        }

        // Fills the wanted sets from where the pointer and the colonists are now.
        private static void Gather(Map map)
        {
            IsoRimSettings st = IsoRimMod.Settings;
            wantWalls.Clear();
            wantTrees.Clear();
            wantRoofs.Clear();
            pointerFoci.Clear();
            colonistFoci.Clear();

            Vector3 mouse = Input.mousePosition;
            bool pointer = !PointerOnInterface();
            Vector3 ground = View3D.ScreenToGround(new Vector2(mouse.x, mouse.y));
            if (pointer)
            {
                pointerFoci.Add(ground);
            }
            if (st.cutNearColonists || st.treesNearColonists || st.roofOverColonists)
            {
                var pawns = map.mapPawns.FreeColonistsSpawned;
                for (int i = 0; i < pawns.Count; i++)
                {
                    colonistFoci.Add(pawns[i].DrawPos);
                }
            }

            if (st.walls3D)
            {
                if (st.cutHover)
                {
                    AddWalls(map, pointerFoci, st.dissolveRadius, st.cutFrontOnly);
                }
                if (st.cutNearColonists)
                {
                    AddWalls(map, colonistFoci, st.colonistRadius, true);
                }
            }
            if (st.trees3D)
            {
                if (st.treesNearPointer)
                {
                    AddTrees(map, pointerFoci, st.treeRadius);
                }
                if (st.treesNearColonists)
                {
                    AddTrees(map, colonistFoci, st.treeRadius);
                }
            }
            if (st.showRoofs)
            {
                rooms.Clear();
                if (st.roofHover && pointer)
                {
                    AddRoom(map, ground.ToIntVec3());
                }
                if (st.roofOverColonists)
                {
                    for (int i = 0; i < colonistFoci.Count; i++)
                    {
                        AddRoom(map, colonistFoci[i].ToIntVec3());
                    }
                }
                foreach (Room room in rooms)
                {
                    foreach (IntVec3 c in room.Cells)
                    {
                        wantRoofs.Add(c);
                    }
                    foreach (IntVec3 c in room.BorderCells)
                    {
                        wantRoofs.Add(c);
                    }
                }
            }
        }

        private static void AddRoom(Map map, IntVec3 c)
        {
            if (!c.InBounds(map))
            {
                return;
            }
            Room room = c.GetRoom(map);
            if (room == null || room.PsychologicallyOutdoors || room.CellCount > 2500)
            {
                return;
            }
            rooms.Add(room);
        }

        // Cuttable walls within reach of each point; with frontOnly, only those between the point and the camera.
        private static void AddWalls(Map map, List<Vector3> foci, float radius, bool frontOnly)
        {
            Vector3 forward = View3D.GroundForward;
            for (int k = 0; k < foci.Count; k++)
            {
                Vector3 f = foci[k];
                for (int x = Mathf.FloorToInt(f.x - radius); x <= Mathf.CeilToInt(f.x + radius); x++)
                {
                    for (int z = Mathf.FloorToInt(f.z - radius); z <= Mathf.CeilToInt(f.z + radius); z++)
                    {
                        float dx = x + 0.5f - f.x;
                        float dz = z + 0.5f - f.z;
                        if (dx * dx + dz * dz > radius * radius)
                        {
                            continue;
                        }
                        if (frontOnly && dx * forward.x + dz * forward.z > 0.6f)
                        {
                            continue;   // behind the point, as the camera sees it
                        }
                        IntVec3 c = new IntVec3(x, 0, z);
                        if (Cuttable(map, c) > 0f)
                        {
                            wantWalls.Add(c);
                        }
                    }
                }
            }
        }

        // Trees within reach of each point, a little further toward the camera, where they hide it.
        private static void AddTrees(Map map, List<Vector3> foci, float radius)
        {
            Vector3 forward = View3D.GroundForward;
            for (int k = 0; k < foci.Count; k++)
            {
                Vector3 f = foci[k] - forward * (radius * 0.4f);
                float r = radius * 1.2f;
                for (int x = Mathf.FloorToInt(f.x - r); x <= Mathf.CeilToInt(f.x + r); x++)
                {
                    for (int z = Mathf.FloorToInt(f.z - r); z <= Mathf.CeilToInt(f.z + r); z++)
                    {
                        float dx = x + 0.5f - f.x;
                        float dz = z + 0.5f - f.z;
                        if (dx * dx + dz * dz > r * r)
                        {
                            continue;
                        }
                        IntVec3 c = new IntVec3(x, 0, z);
                        if (!c.InBounds(map))
                        {
                            continue;
                        }
                        Plant plant = c.GetPlant(map);
                        if (plant != null && plant.def.plant != null && plant.def.plant.IsTree)
                        {
                            wantTrees.Add(c);
                        }
                    }
                }
            }
        }

        // The full height of a wall or door in this cell that can be cut down, or 0.
        private static float Cuttable(Map map, IntVec3 c)
        {
            if (!c.InBounds(map))
            {
                return 0f;
            }
            Building b = c.GetEdifice(map);
            if (b == null)
            {
                return 0f;
            }
            if (b is Building_Door)
            {
                string name = b.def.defName ?? "";
                return name.Contains("Gate") || name.Contains("Fence") ? 0f : View3D.WallHeight;
            }
            ThingForm form = Forms.For(b.def);
            return form.form == Form3D.Block && WallBoxes.CanBeCut(b.def) ? form.height : 0f;
        }

        // The walls of the block holding the cell: just the wall layer, or (if walls are drawn
        // from the game's own sprites) everything in the block.
        private static void RedrawWalls(Map map, IntVec3 cell)
        {
            if (IsoRimMod.Settings.texturedWalls)
            {
                RedrawLayer(map, cell, typeof(SectionLayer_IsoRimWalls));
            }
            else
            {
                Redraw(map, cell, true);
            }
            if (IsoRimMod.Settings.damage3D)
            {
                RedrawLayer(map, cell, typeof(SectionLayer_IsoRimDamage));   // marks move with a cut wall's top
            }
        }

        // Redraws one layer of the block that holds the given cell.
        public static void RedrawLayer(Map map, IntVec3 cell, Type layerType)
        {
            Look();
            if (sectionAt == null || getLayer == null || map == null || map.mapDrawer == null || !cell.InBounds(map))
            {
                return;
            }
            try
            {
                object section = sectionAt.Invoke(map.mapDrawer, new object[] { cell });
                SectionLayer layer = section != null ? getLayer.Invoke(section, new object[] { layerType }) as SectionLayer : null;
                if (layer != null)
                {
                    layer.Regenerate();
                }
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Redrawing part of the map failed: " + e, 93611073);
            }
        }

        public static void RoofChanged(Map map, IntVec3 c)
        {
            if (map == null)
            {
                return;
            }
            // The walls that depend on this cell are the ones just in front of it.
            Vector3 f = View3D.GroundForward;
            int dx = f.x > 0.3f ? 1 : (f.x < -0.3f ? -1 : 0);
            int dz = f.z > 0.3f ? 1 : (f.z < -0.3f ? -1 : 0);
            Note(map, c.x - dx, c.z);
            Note(map, c.x, c.z - dz);
            Note(map, c.x - dx, c.z - dz);
        }

        private static void Note(Map map, int x, int z)
        {
            if (x < 0 || z < 0 || x >= map.Size.x || z >= map.Size.z)
            {
                return;
            }
            int sx = x / SectionSize;
            int sz = z / SectionSize;
            for (int i = 0; i < queue.Count; i++)
            {
                if (queue[i].map == map && queue[i].sx == sx && queue[i].sz == sz)
                {
                    return;
                }
            }
            Pending p = new Pending();
            p.map = map;
            p.sx = sx;
            p.sz = sz;
            p.due = Time.realtimeSinceStartup + 0.6f;   // roofs go up a cell at a time; wait for the rest
            queue.Add(p);
        }

        // Called every frame: redraws at most two waiting blocks.
        public static void Process()
        {
            if (queue.Count == 0)
            {
                return;
            }
            float now = Time.realtimeSinceStartup;
            int done = 0;
            for (int i = queue.Count - 1; i >= 0 && done < 2; i--)
            {
                Pending p = queue[i];
                if (p.due > now)
                {
                    continue;
                }
                queue.RemoveAt(i);
                done++;
                RedrawWalls(p.map, new IntVec3(p.sx * SectionSize + 1, 0, p.sz * SectionSize + 1));
            }
        }

        // Redraws the block of the map that holds the given cell: just its things (walls,
        // furniture, plants) if thingsOnly and the game allows that, otherwise all of it.
        private static void Look()
        {
            if (looked)
            {
                return;
            }
            looked = true;
            sectionAt = AccessTools.Method(typeof(MapDrawer), "SectionAt", new[] { typeof(IntVec3) });
            Type section = AccessTools.TypeByName("Verse.Section");
            regenerate = section != null ? AccessTools.Method(section, "RegenerateAllLayers") : null;
            getLayer = section != null ? AccessTools.Method(section, "GetLayer", new[] { typeof(Type) }) : null;
            thingsLayer = AccessTools.TypeByName("Verse.SectionLayer_ThingsGeneral");
            regenerateLayer = AccessTools.Method(typeof(SectionLayer), "Regenerate", new Type[0]);
            if (sectionAt == null || regenerate == null)
            {
                ModLog.Warn("[IsoRim] The game's way of redrawing one block of the map was not found. Lowered walls will only catch up when something else nearby changes.");
            }
        }

        private static void Redraw(Map map, IntVec3 cell, bool thingsOnly)
        {
            Look();
            if (sectionAt == null || regenerate == null)
            {
                return;
            }
            try
            {
                if (map == null || map.mapDrawer == null || !cell.InBounds(map))
                {
                    return;
                }
                object section = sectionAt.Invoke(map.mapDrawer, new object[] { new IntVec3(cell.x, 0, cell.z) });
                if (section == null)
                {
                    return;
                }
                if (thingsOnly && getLayer != null && thingsLayer != null && regenerateLayer != null)
                {
                    object layer = getLayer.Invoke(section, new object[] { thingsLayer });
                    if (layer != null)
                    {
                        regenerateLayer.Invoke(layer, null);
                        return;
                    }
                }
                regenerate.Invoke(section, null);
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Redrawing part of the map failed: " + e, 93611071);
            }
        }
    }

    // The blades of a wind turbine: a separate model spun round its hub at a speed that follows
    // the power the turbine is making, in place of the flat blades the game draws.
    public static class Turbines
    {
        private const float HubHeight = 2.75f;    // where the hub is on the turbine model
        private const float HubForward = -0.62f;

        private static bool tried;
        private static Model rotor;
        private static readonly Dictionary<int, float> spin = new Dictionary<int, float>();

        // comp is the turbine's power component. Returns false if nothing was drawn.
        public static bool Draw(ThingComp comp)
        {
            Thing parent = comp != null ? comp.parent : null;
            if (parent == null || parent.def == null || !IsoRimMod.Settings.models3D)
            {
                return false;
            }
            ModelEntry entry;
            if (!ModelLibrary.TryGet(parent.def, out entry) || !entry.HasModel)
            {
                return false;
            }
            if (!tried)
            {
                tried = true;
                if (IsoRimMod.RootDir != null)
                {
                    rotor = ModelLibrary.LoadFile(Path.Combine(IsoRimMod.RootDir, "Models", "wind_rotor.obj"));
                }
            }
            if (rotor == null)
            {
                return false;
            }

            float angle;
            spin.TryGetValue(parent.thingIDNumber, out angle);
            CompPowerTrader power = comp as CompPowerTrader;
            float making = power != null ? Mathf.Clamp(Mathf.Abs(power.PowerOutput) / 2300f, 0f, 1.6f) : 0.5f;
            float gameSpeed = Find.TickManager != null ? Find.TickManager.TickRateMultiplier : 1f;
            angle = Mathf.Repeat(angle + Time.deltaTime * gameSpeed * making * 220f, 360f);
            spin[parent.thingIDNumber] = angle;

            float size = entry.def.scale;
            Vector3 at = parent.DrawPos;
            Matrix4x4 local = Matrix4x4.Translate(new Vector3(0f, 0f, HubForward * size))
                * Matrix4x4.Rotate(Quaternion.AngleAxis(angle, Vector3.forward))
                * Matrix4x4.Scale(new Vector3(size, size, size));
            DynamicModels.DrawLocal(rotor, new Vector3(at.x, HubHeight * size, at.z), parent.Rotation.AsAngle + entry.def.rotation, local, Color.white, null);
            return true;
        }
    }

    // A door drawn as two 3D leaves that slide apart into the walls either side, with a beam
    // across the top that carries the wall line over the doorway. It is as tall as the walls
    // and takes the texture and colour of what the door is built from.
    public static class Doors
    {
        private const float BuiltForWallHeight = 1.2f;

        private static bool tried;
        private static Model leaf;
        private static Model lintel;
        private static Model gateLeaf;
        private static Model gatePosts;

        // openDistance is how far each leaf has slid, in cells (0 = shut). Returns false if the
        // door could not be drawn, so the game draws its own.
        public static bool Draw(Building_Door door, float openDistance)
        {
            if (!tried)
            {
                tried = true;
                string root = IsoRimMod.RootDir;
                if (root != null)
                {
                    leaf = ModelLibrary.LoadFile(Path.Combine(root, "Models", "door_leaf.obj"));
                    lintel = ModelLibrary.LoadFile(Path.Combine(root, "Models", "door_lintel.obj"));
                    gateLeaf = ModelLibrary.LoadFile(Path.Combine(root, "Models", "gate_leaf.obj"));
                    gatePosts = ModelLibrary.LoadFile(Path.Combine(root, "Models", "gate_posts.obj"));
                }
            }
            Map map = door.Map;
            if (leaf == null || map == null)
            {
                return false;
            }

            // The door lies along whichever line has more wall next to it.
            IntVec3 c = door.Position;
            int eastWest = Block(map, c + IntVec3.East) + Block(map, c + IntVec3.West);
            int northSouth = Block(map, c + IntVec3.North) + Block(map, c + IntVec3.South);
            float yaw = eastWest >= northSouth ? 0f : 90f;

            Vector3 along = Quaternion.AngleAxis(yaw, Vector3.up) * Vector3.right;
            Vector3 centre = new Vector3(c.x + 0.5f, 0f, c.z + 0.5f);

            // A gate in a fence: two low leaves between a pair of posts, with no beam over them.
            string defName = door.def.defName ?? "";
            if (gateLeaf != null && (defName.IndexOf("Gate", StringComparison.OrdinalIgnoreCase) >= 0 || defName.Contains("Fence")))
            {
                Color gateTint = door.DrawColor;
                string gateSwatch = R3DTextures.StuffSwatch(door);
                float swing = Mathf.Clamp(openDistance, 0f, 0.44f);
                DynamicModels.DrawLocal(gateLeaf, centre + along * swing, yaw, Matrix4x4.identity, gateTint, gateSwatch);
                DynamicModels.DrawLocal(gateLeaf, centre - along * swing, yaw + 180f, Matrix4x4.identity, gateTint, gateSwatch);
                if (gatePosts != null)
                {
                    DynamicModels.DrawLocal(gatePosts, centre, yaw, Matrix4x4.identity, gateTint, gateSwatch);
                }
                return true;
            }

            // A door in a wall that is cut down is cut down with it.
            float height = View3D.WallHeight;
            if (WallBoxes.CellCut(map, c))
            {
                height *= WallBoxes.CutFraction;
            }
            Matrix4x4 sized = Matrix4x4.Scale(new Vector3(1f, height / BuiltForWallHeight, 1f));
            Color tint = door.DrawColor;
            string swatch = R3DTextures.StuffSwatch(door);
            float open = Mathf.Clamp(openDistance, 0f, 0.48f);

            // The two leaves are the same model, one turned half way round. Drawn this way their
            // shading follows the light, not the model, so both come out the same.
            DynamicModels.DrawLocal(leaf, centre + along * open, yaw, sized, tint, swatch);
            DynamicModels.DrawLocal(leaf, centre - along * open, yaw + 180f, sized, tint, swatch);
            if (lintel != null)
            {
                DynamicModels.DrawLocal(lintel, centre, yaw, sized, tint, swatch);
            }
            return true;
        }

        private static int Block(Map map, IntVec3 cell)
        {
            if (!cell.InBounds(map))
            {
                return 0;
            }
            Building b = cell.GetEdifice(map);
            if (b == null)
            {
                return 0;
            }
            return Forms.For(b.def).form == Form3D.Block || b is Building_Door || (b.def.defName != null && b.def.defName.Contains("Fence")) ? 1 : 0;
        }
    }

    // Flames that flicker and smoke and steam that rise, built from small 3D shapes in the same
    // style as everything else and moved a little every frame: over campfires (while they have
    // fuel) and over steam geysers (unless a generator sits on them).
    public static class Effects
    {
        private static bool tried;
        private static Model flame;
        private static Model flameCore;
        private static Model puff;
        private static ThingDef campfire;
        private static ThingDef geyser;

        // Called every frame while the 3D view is on.
        public static void DrawAll()
        {
            IsoRimSettings st = IsoRimMod.Settings;
            Map map = Find.CurrentMap;
            if (!st.effects3D || !st.models3D || map == null || Find.TickManager == null)
            {
                return;
            }
            if (!tried)
            {
                tried = true;
                string root = IsoRimMod.RootDir;
                if (root != null)
                {
                    flame = ModelLibrary.LoadFile(Path.Combine(root, "Models", "fx_flame.obj"));
                    flameCore = ModelLibrary.LoadFile(Path.Combine(root, "Models", "fx_flame_core.obj"));
                    puff = ModelLibrary.LoadFile(Path.Combine(root, "Models", "fx_puff.obj"));
                }
                campfire = DefDatabase<ThingDef>.GetNamedSilentFail("Campfire");
                geyser = DefDatabase<ThingDef>.GetNamedSilentFail("SteamGeyser");
            }
            try
            {
                // Time in seconds of game time, so everything stands still while the game is paused.
                float t = Find.TickManager.TicksGame / 60f;
                float wind = map.windManager != null ? Mathf.Clamp(map.windManager.WindSpeed, 0f, 2f) : 0.5f;
                CellRect view = Find.CameraDriver.CurrentViewRect.ExpandedBy(4);

                if (campfire != null && puff != null)
                {
                    List<Thing> fires = map.listerThings.ThingsOfDef(campfire);
                    for (int i = 0; i < fires.Count; i++)
                    {
                        if (view.Contains(fires[i].Position))
                        {
                            Campfire(fires[i], t, wind);
                        }
                    }
                }
                if (st.waterStyle)
                {
                    Sparkles(map, view, t);
                }
                if (geyser != null && puff != null)
                {
                    List<Thing> vents = map.listerThings.ThingsOfDef(geyser);
                    for (int i = 0; i < vents.Count; i++)
                    {
                        if (view.Contains(vents[i].Position))
                        {
                            Geyser(vents[i], map, t, wind);
                        }
                    }
                }
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Drawing flames and smoke failed: " + e, 93611080);
            }
        }

        private static Mesh glint;

        // Little stars of light that wink on and off across open water, in three groups that take
        // turns so the surface always has a few. Which cells sparkle is picked afresh each time.
        // The open water cells of the current map, looked up again now and then, so the sparkles
        // never have to search the whole view.
        private static bool[] waterGrid;
        private static int waterCount;
        private static Map waterMap;
        private static int waterFrame = -100000;

        private static void Sparkles(Map map, CellRect view, float t)
        {
            if (glint == null)
            {
                glint = MakeGlint();
            }
            Material mat = R3DMaterials.Solid;
            if (mat == null)
            {
                return;
            }
            int frame = Time.frameCount;
            if (map != waterMap || waterGrid == null || frame - waterFrame > 2500)
            {
                waterMap = map;
                waterFrame = frame;
                int n = map.cellIndices.NumGridCells;
                if (waterGrid == null || waterGrid.Length != n)
                {
                    waterGrid = new bool[n];
                }
                waterCount = 0;
                TerrainGrid terrain = map.terrainGrid;
                for (int i = 0; i < n; i++)
                {
                    bool w = Ground.IsWater(terrain.TerrainAt(i));
                    waterGrid[i] = w;
                    if (w)
                    {
                        waterCount++;
                    }
                }
            }
            if (waterCount == 0)
            {
                return;
            }
            view = view.ClipInsideMap(map);
            CellIndices indices = map.cellIndices;
            float y = AltitudeLayer.Terrain.AltitudeFor() + 0.02f;
            for (int g = 0; g < 3; g++)
            {
                float clockT = t * 0.8f + g / 3f;
                int slot = Mathf.FloorToInt(clockT);
                float size = Mathf.Sin((clockT - slot) * Mathf.PI) * 0.17f;
                if (size < 0.025f)
                {
                    continue;
                }
                int salt = (slot * 3 + g) & 0xFFFF;
                for (int z = view.minZ; z <= view.maxZ; z++)
                {
                    for (int x = view.minX; x <= view.maxX; x++)
                    {
                        if (!waterGrid[indices.CellToIndex(x, z)] || Hashing.Unit(x, z, salt) < 0.985f)
                        {
                            continue;
                        }
                        Vector3 at = new Vector3(x + 0.15f + 0.7f * Hashing.Unit(x, z, salt + 1), y, z + 0.15f + 0.7f * Hashing.Unit(x, z, salt + 2));
                        float k = size * (0.7f + 0.6f * Hashing.Unit(x, z, salt + 3));
                        Graphics.DrawMesh(glint, Matrix4x4.TRS(at, Quaternion.identity, new Vector3(k, 1f, k)), mat, 0);
                    }
                }
            }
        }

        // A flat four-pointed star one unit across.
        private static Mesh MakeGlint()
        {
            List<Vector3> v = new List<Vector3>();
            List<Color32> c = new List<Color32>();
            List<int> tris = new List<int>();
            Color32 white = new Color32(246, 252, 255, 255);
            v.Add(Vector3.zero);
            c.Add(white);
            for (int i = 0; i < 8; i++)
            {
                float a = i * Mathf.PI / 4f;
                float r = i % 2 == 0 ? 0.5f : 0.12f;
                v.Add(new Vector3(Mathf.Cos(a) * r, 0f, Mathf.Sin(a) * r));
                c.Add(white);
            }
            for (int i = 0; i < 8; i++)
            {
                tris.Add(0);
                tris.Add(1 + (i + 1) % 8);
                tris.Add(1 + i);
            }
            Mesh m = new Mesh();
            m.name = "IsoRim_Glint";
            m.SetVertices(v);
            m.SetColors(c);
            m.SetTriangles(tris, 0);
            m.RecalculateBounds();
            return m;
        }

        private static void Campfire(Thing fire, float t, float wind)
        {
            ModelEntry entry;
            if (!ModelLibrary.TryGet(fire.def, out entry) || !entry.HasModel)
            {
                return;
            }
            CompRefuelable fuel = fire.TryGetComp<CompRefuelable>();
            if (fuel != null && !fuel.HasFuel)
            {
                return;   // burnt out
            }
            Vector3 at = fire.DrawPos;
            Vector3 foot = new Vector3(at.x, 0f, at.z);
            float own = fire.thingIDNumber * 0.37f;

            // Three tongues of flame round a brighter heart, each flickering to its own beat.
            if (flame != null)
            {
                for (int i = 0; i < 3; i++)
                {
                    float beat = t * (7.0f + i * 1.7f) + own + i * 2.1f;
                    float tall = 0.62f + 0.13f * Mathf.Sin(beat) + 0.05f * Mathf.Sin(beat * 2.3f);
                    float wide = 0.30f - 0.035f * Mathf.Sin(beat * 1.3f);
                    float a = i * 2.094f + 0.3f * Mathf.Sin(beat * 0.5f);
                    Matrix4x4 local = Matrix4x4.Translate(new Vector3(0.07f * Mathf.Cos(a), 0.07f, 0.07f * Mathf.Sin(a)))
                        * Matrix4x4.Scale(new Vector3(wide, tall, wide));
                    DynamicModels.DrawLocal(flame, foot, t * 50f * (i % 2 == 0 ? 1f : -1f) + i * 40f, local, Color.white, null);
                }
            }
            if (flameCore != null)
            {
                float beat = t * 11f + own;
                Matrix4x4 local = Matrix4x4.Translate(new Vector3(0f, 0.08f, 0f))
                    * Matrix4x4.Scale(new Vector3(0.18f, 0.40f + 0.07f * Mathf.Sin(beat), 0.18f));
                DynamicModels.DrawLocal(flameCore, foot, t * 90f, local, Color.white, null);
            }

            Rise(foot, t * 0.30f + own, 5, 0.75f, 2.3f, 0.15f, 0.44f, 0.35f + 0.5f * wind, 0.30f, 0.60f);
        }

        private static void Geyser(Thing vent, Map map, float t, float wind)
        {
            ModelEntry entry;
            if (!ModelLibrary.TryGet(vent.def, out entry) || !entry.HasModel)
            {
                return;
            }
            // A geothermal generator built over the vent caps it.
            Building over = vent.Position.GetEdifice(map);
            if (over != null && over != vent && over.def.defName != null && over.def.defName.Contains("Geothermal"))
            {
                return;
            }
            Vector3 at = vent.DrawPos;
            Vector3 foot = new Vector3(at.x, 0f, at.z);
            float own = vent.thingIDNumber * 0.53f;
            Rise(foot, t * 0.42f + own, 7, 0.15f, 3.4f, 0.30f, 0.95f, 0.25f + 0.6f * wind, 0.86f, 0.97f);
        }

        // A column of puffs, each rising from 'from' to 'from + climb' above the ground, growing
        // from small to big, leaning with the wind, and shrinking away at the top. grey0 and
        // grey1 are its shade at the bottom and at the top.
        private static void Rise(Vector3 foot, float clock, int count, float from, float climb, float small, float big, float lean, float grey0, float grey1)
        {
            for (int i = 0; i < count; i++)
            {
                float u = Mathf.Repeat(clock + (float)i / count, 1f);
                float size = Mathf.Lerp(small, big, u) * Mathf.Clamp01(u / 0.12f) * Mathf.Clamp01((1f - u) / 0.28f);
                if (size < 0.02f)
                {
                    continue;
                }
                float wobble = clock * 6.28f * 0.7f + i * 1.9f;
                Vector3 p = new Vector3(
                    foot.x + lean * u * u + 0.07f * Mathf.Sin(wobble) * (0.3f + u),
                    from + climb * u,
                    foot.z + 0.25f * lean * u * u + 0.07f * Mathf.Cos(wobble * 1.3f) * (0.3f + u));
                float g = Mathf.Lerp(grey0, grey1, u);
                DynamicModels.DrawLocal(puff, p, i * 67f + clock * 40f, Matrix4x4.Scale(new Vector3(size, size * 0.9f, size)), new Color(g, g, g * 1.02f), null);
            }
        }
    }
}
