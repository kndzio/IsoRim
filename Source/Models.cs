using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Reflection;
using HarmonyLib;
using UnityEngine;
using UnityEngine.Rendering;
using Verse;

namespace IsoRim
{
    // XML settings for how one thing is drawn in 3D. Any mod can add these:
    //
    //   <IsoRim.ModelDef>
    //     <defName>R3D_TorchLamp</defName>
    //     <thingDef>TorchLamp</thingDef>
    //     <model>Models/torch_lamp.obj</model>   (path inside the mod that contains this def)
    //   </IsoRim.ModelDef>
    //
    // Leave <model> out to keep the automatic shape and only change it with <height> or <flat>.
    public class ModelDef : Def
    {
        public string thingDef;
        public string model;
        public float scale = 1f;
        public Vector3 offset = Vector3.zero;
        public float rotation = 0f;         // extra turn around the vertical axis, degrees
        public float surfaceHeight = -1f;   // where a pawn lying on it rests; -1 uses the top of the model
        public float height = -1f;          // height in cells of the automatic shape; -1 lets the mod decide
        public bool flat = false;           // true keeps the thing as a flat sprite

        public List<string> models;         // several models: each thing picks one and keeps it
        public string thingCategory;        // apply to every thing in this category instead of one thingDef
        public bool randomRotation = false; // give each thing its own turn
        public float scaleJitter = 0f;      // vary each thing's size by up to this fraction
        public bool growthScale = false;    // scale with how grown a plant is
        public bool layFlat = false;        // the model is built as held; on the ground it is tipped onto its side
        public float scatter = 0f;          // move each thing up to this far (in cells) off the middle of its cell
        public bool spriteTint = false;     // colour "stuff" parts from the thing's own sprite instead of its material
        public string fallback;             // "SmallPlants": every plant that is not a tree and has no other entry

        public bool wallMounted = false;    // fixed to the wall the thing faces (wall lamps)
        public float mountHeight = 0.5f;    // how far up that wall, as a fraction of the wall's height
        public bool alongRun = false;       // turned a quarter turn where its row runs north-south (sandbags)
        public bool fullVariant = false;    // the second model is used once the thing holds something (graves)
        public bool groundShadow = true;    // soft shading on the ground under it
        public float outline = 1f;          // how bold the dark outline is; 0 for none
        public bool linked = false;         // the first model stands in the cell; the second is added toward each neighbour it joins

        // Matching by name: every building or item whose defName contains any of these (ignoring
        // case) and that has no entry of its own or of its category. Used for the wrecks and junk
        // that other content scatters over maps, whose exact names vary.
        public List<string> match;
        public Vector2 builtFor = Vector2.zero; // the footprint (x, z) in cells the model was built for; it is stretched to the thing's real size
        public string topModel;             // turrets: the gun that turns, drawn every frame
        public float topHeight = 0.5f;      // height of the turret's pivot, in cells

        // Animals. thingDef is the animal's race; model is its body, facing north.
        public bool animal = false;
        public string legModel;             // one leg, standing on the ground with its hip at the top
        public List<Vector3> legs;          // where each hip is on the body
        public float legLength = 0f;        // height of the hip above the foot
        public float legSwing = 26f;        // how far the legs swing when walking, degrees
        public float legSplay = 0f;         // how far the legs lean outward (lizards, insects), degrees
        public float stride = 1f;           // cells walked for one full swing of the legs
        public float bodyCentre = 0f;       // height of the middle of the trunk
        public float bodyHalfWidth = 0.2f;  // half the width of the trunk; where it rests when on its side
        public float bodyHalfLength = 0.4f; // half the length of the animal, for the shading under it
    }

    // Triangle soup: every three entries make one triangle, already in game axes
    // (X east, Y up, Z north), one cell per unit, centred on the thing's footprint.
    public class Model
    {
        public Vector3[] positions;
        public Vector3[] normals;
        public Color[] colors;
        public bool[] tinted;   // true where the colour is multiplied by the thing's stuff colour
        public Vector2[] uvs;   // texture coordinates
        public int[] material;  // which entry of materials each vertex uses
        public ModelMaterial[] materials;
        public Vector3[] hull;  // how far each vertex moves outward to form the dark outline
        public float maxY;
        public float halfDepth; // furthest the model reaches north or south of its centre
        public float minX, maxX, minZ, maxZ;   // the box the model covers on the ground
        public int id;          // unique per loaded model
        public ShadowShape shadow;   // worked out the first time the model has to cast a shadow
        public bool shadowTried;
        public Vector2[] footprint;      // outline of the model seen from above, and of the model
        public Vector2[] footprintLaid;  // tipped onto its side; worked out when first needed
        public bool footprintTried;
    }

    // A simple stand-in for a model when it casts a shadow: the outline of its leaves seen from
    // above, held at one height, on top of a square post for the trunk. Flat pieces like these
    // never lie over themselves however the sun moves them, which the real model's hundreds of
    // faces would.
    public class ShadowShape
    {
        public Vector2[] crown;     // corners of the leaf outline (x, z), anticlockwise; null if there are no leaves
        public float crownHeight;
        public float trunkHalf;     // half the width of the trunk
        public float trunkTop;      // the height of everything that is not a leaf

        public static ShadowShape For(Model m)
        {
            if (!m.shadowTried)
            {
                m.shadowTried = true;
                try
                {
                    m.shadow = Build(m);
                }
                catch (Exception e)
                {
                    m.shadow = null;
                    Log.ErrorOnce("[IsoRim] Working out a model's shadow failed: " + e, 93611061);
                }
            }
            return m.shadow;
        }

        // The outline of the ground a model covers, corners anticlockwise in (x, z); null if it has none.
        public static Vector2[] Footprint(Model m, bool laid)
        {
            if (!m.footprintTried)
            {
                m.footprintTried = true;
                try
                {
                    List<Vector2> standing = new List<Vector2>(m.positions.Length);
                    List<Vector2> tipped = new List<Vector2>(m.positions.Length);
                    for (int i = 0; i < m.positions.Length; i++)
                    {
                        Vector3 p = m.positions[i];
                        standing.Add(new Vector2(p.x, p.z));
                        tipped.Add(new Vector2(p.x, p.y));   // tipped over, what was up points north
                    }
                    Vector2[] a = Hull(standing);
                    Vector2[] b = Hull(tipped);
                    m.footprint = a.Length >= 3 ? a : null;
                    m.footprintLaid = b.Length >= 3 ? b : null;
                }
                catch (Exception e)
                {
                    m.footprint = null;
                    m.footprintLaid = null;
                    Log.ErrorOnce("[IsoRim] Working out a model's footprint failed: " + e, 93611062);
                }
            }
            return laid ? m.footprintLaid : m.footprint;
        }

        private static ShadowShape Build(Model m)
        {
            int n = m.positions.Length;
            bool[] leaf = new bool[n];
            List<Vector2> leaves = new List<Vector2>();
            float leafLow = float.MaxValue;
            float leafHigh = 0f;
            float woodTop = 0f;
            for (int i = 0; i < n; i++)
            {
                Vector3 p = m.positions[i];
                ModelMaterial mm = m.materials != null && m.material != null ? m.materials[m.material[i]] : null;
                leaf[i] = mm != null && mm.leaf;
                if (leaf[i])
                {
                    leaves.Add(new Vector2(p.x, p.z));
                    leafLow = Mathf.Min(leafLow, p.y);
                    leafHigh = Mathf.Max(leafHigh, p.y);
                }
                else
                {
                    woodTop = Mathf.Max(woodTop, p.y);
                }
            }

            // The trunk is as wide as the woody part is in its bottom third.
            float limit = Mathf.Max(0.05f, woodTop * 0.33f);
            float half = 0f;
            for (int i = 0; i < n; i++)
            {
                Vector3 p = m.positions[i];
                if (!leaf[i] && p.y <= limit)
                {
                    half = Mathf.Max(half, Mathf.Max(Mathf.Abs(p.x), Mathf.Abs(p.z)));
                }
            }

            ShadowShape s = new ShadowShape();
            s.trunkHalf = Mathf.Clamp(half * 0.8f, 0.02f, 0.25f);
            s.trunkTop = woodTop;
            if (leaves.Count >= 3)
            {
                Vector2[] hull = Hull(leaves);
                if (hull.Length >= 3)
                {
                    s.crown = hull;
                    s.crownHeight = leafLow + (leafHigh - leafLow) * 0.45f;
                }
            }
            if (s.crown == null && woodTop <= 0.01f)
            {
                return null;   // nothing to cast a shadow
            }
            return s;
        }

        // The smallest outline with no dents that holds every point, corners in anticlockwise order.
        private static Vector2[] Hull(List<Vector2> points)
        {
            points.Sort(delegate (Vector2 a, Vector2 b)
            {
                int c = a.x.CompareTo(b.x);
                return c != 0 ? c : a.y.CompareTo(b.y);
            });
            int n = points.Count;
            Vector2[] h = new Vector2[2 * n];
            int k = 0;
            for (int i = 0; i < n; i++)
            {
                while (k >= 2 && Cross(h[k - 2], h[k - 1], points[i]) <= 1e-9f)
                {
                    k--;
                }
                h[k++] = points[i];
            }
            int lower = k + 1;
            for (int i = n - 2; i >= 0; i--)
            {
                while (k >= lower && Cross(h[k - 2], h[k - 1], points[i]) <= 1e-9f)
                {
                    k--;
                }
                h[k++] = points[i];
            }
            int count = Mathf.Max(0, k - 1);   // the last point repeats the first
            Vector2[] result = new Vector2[count];
            Array.Copy(h, result, count);
            return result;
        }

        private static float Cross(Vector2 o, Vector2 a, Vector2 b)
        {
            return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
        }
    }

    public class ModelMaterial
    {
        public string name = "";
        public string texture;   // path under Textures/ without extension; null for a plain colour
        public Color color = new Color(0.8f, 0.8f, 0.8f);
        public bool tinted;
        public bool leaf;        // left out while a tree is bare
        public bool twig;        // only drawn while a tree is bare (fine branches the leaves would hide)
        public bool glow;        // gives off its own light (flames, embers, lamps): never shaded
    }

    public class ModelEntry
    {
        public ModelDef def;
        public Model[] variants;
        public Model leg;   // animals only
        public Model top;   // turrets only

        public bool HasModel
        {
            get { return variants != null && variants.Length > 0; }
        }

        // True if the model was built long east-west but the thing is long north-south (or the
        // other way round): it is then turned a quarter turn to fit.
        public bool Swapped(ThingDef thing)
        {
            if (def.builtFor.x <= 0f || def.builtFor.y <= 0f || thing == null || Mathf.Approximately(def.builtFor.x, def.builtFor.y)
                || thing.size.x == thing.size.z)
            {
                return false;
            }
            return (def.builtFor.x > def.builtFor.y) != (thing.size.x > thing.size.z);
        }

        // How much the model is stretched along x, up and along z to fit a thing of this kind:
        // (1, 1, 1) unless the model was built for a different footprint.
        public Vector3 Fit(ThingDef thing)
        {
            if (def.builtFor.x <= 0f || def.builtFor.y <= 0f || thing == null)
            {
                return Vector3.one;
            }
            bool swap = Swapped(thing);
            float sx = (swap ? thing.size.z : thing.size.x) / def.builtFor.x;
            float sz = (swap ? thing.size.x : thing.size.z) / def.builtFor.y;
            if (Mathf.Abs(sx - 1f) < 0.01f && Mathf.Abs(sz - 1f) < 0.01f)
            {
                return Vector3.one;
            }
            return new Vector3(sx, Mathf.Sqrt(sx * sz), sz);
        }

        // The same thing always gets the same variant.
        public Model Pick(Thing t)
        {
            if (!HasModel)
            {
                return null;
            }
            int n = t != null ? t.thingIDNumber : 0;
            if (n < 0)
            {
                n = -n;
            }
            return variants[n % variants.Length];
        }

        public float SurfaceHeight
        {
            get
            {
                if (def.surfaceHeight >= 0f)
                {
                    return def.surfaceHeight;
                }
                return HasModel ? variants[0].maxY * def.scale : 0f;
            }
        }
    }

    public static class ModelLibrary
    {
        private static readonly Dictionary<ThingDef, ModelEntry> byThing = new Dictionary<ThingDef, ModelEntry>();
        private static readonly Dictionary<string, Model> byPath = new Dictionary<string, Model>();

        public static bool TryGet(ThingDef def, out ModelEntry entry)
        {
            return byThing.TryGetValue(def, out entry);
        }

        // Loads a model file once; null if it is missing or unreadable.
        public static Model LoadFile(string path)
        {
            Model model;
            if (byPath.TryGetValue(path, out model))
            {
                return model;
            }
            try
            {
                model = ObjLoader.Load(path);
            }
            catch (Exception e)
            {
                ModLog.Warn("[IsoRim] Could not read model " + path + ": " + e.Message);
                model = null;
            }
            byPath[path] = model;
            return model;
        }

        private static ModelEntry MakeEntry(ModelDef md)
        {
            List<string> files = new List<string>();
            if (!md.model.NullOrEmpty())
            {
                files.Add(md.model);
            }
            if (md.models != null)
            {
                files.AddRange(md.models);
            }

            List<Model> loaded = new List<Model>();
            if (md.modContentPack != null)
            {
                for (int i = 0; i < files.Count; i++)
                {
                    Model m = LoadFile(Path.Combine(md.modContentPack.RootDir, files[i]));
                    if (m != null)
                    {
                        loaded.Add(m);
                    }
                }
            }

            ModelEntry entry = new ModelEntry();
            entry.def = md;
            entry.variants = loaded.ToArray();
            if (!md.legModel.NullOrEmpty() && md.modContentPack != null)
            {
                entry.leg = LoadFile(Path.Combine(md.modContentPack.RootDir, md.legModel));
            }
            if (!md.topModel.NullOrEmpty() && md.modContentPack != null)
            {
                entry.top = LoadFile(Path.Combine(md.modContentPack.RootDir, md.topModel));
            }
            return entry;
        }

        public static void LoadAll()
        {
            List<ModelDef> all = DefDatabase<ModelDef>.AllDefsListForReading;

            // Entries naming one thing come first, so they win over a category the thing is in.
            for (int i = 0; i < all.Count; i++)
            {
                ModelDef md = all[i];
                if (md.thingDef.NullOrEmpty())
                {
                    continue;
                }
                // A thing from a DLC or mod that is not installed is skipped quietly.
                ThingDef thing = DefDatabase<ThingDef>.GetNamedSilentFail(md.thingDef);
                if (thing != null)
                {
                    byThing[thing] = MakeEntry(md);
                }
            }

            for (int i = 0; i < all.Count; i++)
            {
                ModelDef md = all[i];
                if (md.thingCategory.NullOrEmpty())
                {
                    continue;
                }
                ThingCategoryDef category = DefDatabase<ThingCategoryDef>.GetNamedSilentFail(md.thingCategory);
                if (category == null)
                {
                    continue;
                }
                ModelEntry entry = null;
                foreach (ThingDef thing in DefDatabase<ThingDef>.AllDefs)
                {
                    if (thing.thingCategories == null || !thing.thingCategories.Contains(category) || byThing.ContainsKey(thing))
                    {
                        continue;
                    }
                    if (entry == null)
                    {
                        entry = MakeEntry(md);
                    }
                    byThing[thing] = entry;
                }
            }

            // Then names: the wrecks, junk and ruins other content scatters about. Earlier entries win.
            for (int i = 0; i < all.Count; i++)
            {
                ModelDef md = all[i];
                if (md.match == null || md.match.Count == 0)
                {
                    continue;
                }
                ModelEntry entry = null;
                foreach (ThingDef thing in DefDatabase<ThingDef>.AllDefs)
                {
                    if (byThing.ContainsKey(thing) || thing.defName == null || thing.IsBlueprint || thing.IsFrame
                        || (thing.category != ThingCategory.Building && thing.category != ThingCategory.Item))
                    {
                        continue;
                    }
                    bool hit = false;
                    for (int k = 0; k < md.match.Count && !hit; k++)
                    {
                        hit = !md.match[k].NullOrEmpty() && thing.defName.IndexOf(md.match[k], StringComparison.OrdinalIgnoreCase) >= 0;
                    }
                    if (!hit)
                    {
                        continue;
                    }
                    if (entry == null)
                    {
                        entry = MakeEntry(md);
                    }
                    byThing[thing] = entry;
                }
            }

            // Last, the catch-all for small plants: grass, flowers and crops from DLC and other mods.
            for (int i = 0; i < all.Count; i++)
            {
                ModelDef md = all[i];
                if (md.fallback != "SmallPlants")
                {
                    continue;
                }
                ModelEntry entry = null;
                foreach (ThingDef thing in DefDatabase<ThingDef>.AllDefs)
                {
                    if (thing.category != ThingCategory.Plant || thing.plant == null || thing.plant.IsTree || byThing.ContainsKey(thing))
                    {
                        continue;
                    }
                    // Tree stumps and burned trees are plants too, but a clump of leaves would not suit them.
                    if (thing.defName.Contains("Stump") || thing.defName.Contains("Burned"))
                    {
                        continue;
                    }
                    if (entry == null)
                    {
                        entry = MakeEntry(md);
                    }
                    byThing[thing] = entry;
                }
            }

            int models = 0;
            foreach (KeyValuePair<ThingDef, ModelEntry> pair in byThing)
            {
                if (pair.Value.HasModel)
                {
                    models++;
                }
            }
            ModLog.Debug("[IsoRim] " + models + " things have a hand-made 3D model.");
        }
    }

    // Reads Wavefront OBJ, the plain-text format Blender exports with its default axes
    // (Y up, -Z forward), with its .mtl file. Per material: Kd is the colour, map_Kd an optional
    // texture, and a name starting with "stuff" takes the colour of whatever the thing is made of.
    public static class ObjLoader
    {
        private static readonly char[] Separators = { ' ', '\t' };
        private static readonly Color DefaultColor = new Color(0.8f, 0.8f, 0.8f);
        private const float OutlineWidth = 0.03f;   // in cells
        private static int nextId = 1;

        public static Model Load(string path)
        {
            if (!File.Exists(path))
            {
                ModLog.Warn("[IsoRim] Model file not found: " + path);
                return null;
            }

            List<Vector3> pos = new List<Vector3>();
            List<Vector2> tex = new List<Vector2>();
            List<Color> vertColor = new List<Color>();
            List<bool> hasVertColor = new List<bool>();

            List<ModelMaterial> materials = new List<ModelMaterial>();
            Dictionary<string, int> materialIndex = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
            materials.Add(new ModelMaterial());   // used by faces that name no material
            int current = 0;

            List<Vector3> outPos = new List<Vector3>();
            List<Vector3> outNormal = new List<Vector3>();
            List<Color> outColor = new List<Color>();
            List<bool> outTint = new List<bool>();
            List<Vector2> outUV = new List<Vector2>();
            List<int> outMaterial = new List<int>();

            string dir = Path.GetDirectoryName(path);
            List<int> face = new List<int>();
            List<int> faceUV = new List<int>();

            foreach (string raw in File.ReadAllLines(path))
            {
                string line = raw.Trim();
                if (line.Length == 0 || line[0] == '#')
                {
                    continue;
                }
                string[] t = line.Split(Separators, StringSplitOptions.RemoveEmptyEntries);

                if (t[0] == "mtllib" && t.Length > 1)
                {
                    ReadMaterials(Path.Combine(dir, line.Substring(6).Trim()), materials, materialIndex);
                }
                else if (t[0] == "usemtl")
                {
                    string name = t.Length > 1 ? t[1] : "";
                    if (!materialIndex.TryGetValue(name, out current))
                    {
                        current = AddMaterial(name, materials, materialIndex);
                    }
                }
                else if (t[0] == "v" && t.Length >= 4)
                {
                    // OBJ is right-handed; flipping Z turns it into the game's axes.
                    pos.Add(new Vector3(Num(t[1]), Num(t[2]), -Num(t[3])));
                    if (t.Length >= 7)
                    {
                        vertColor.Add(new Color(Num(t[4]), Num(t[5]), Num(t[6])));
                        hasVertColor.Add(true);
                    }
                    else
                    {
                        vertColor.Add(Color.white);
                        hasVertColor.Add(false);
                    }
                }
                else if (t[0] == "vt" && t.Length >= 3)
                {
                    tex.Add(new Vector2(Num(t[1]), Num(t[2])));
                }
                else if (t[0] == "f" && t.Length >= 4)
                {
                    // Each corner is written as position, position/texture or position/texture/normal.
                    face.Clear();
                    faceUV.Clear();
                    bool bad = false;
                    for (int i = 1; i < t.Length; i++)
                    {
                        string[] parts = t[i].Split('/');
                        int idx = Index(parts[0], pos.Count);
                        if (idx < 0)
                        {
                            bad = true;
                            break;
                        }
                        face.Add(idx);
                        faceUV.Add(parts.Length > 1 ? Index(parts[1], tex.Count) : -1);
                    }
                    if (bad)
                    {
                        continue;
                    }

                    ModelMaterial mat = materials[current];

                    // Split polygons into a fan of triangles.
                    for (int i = 1; i + 1 < face.Count; i++)
                    {
                        Vector3 a = pos[face[0]];
                        Vector3 b = pos[face[i]];
                        Vector3 c = pos[face[i + 1]];
                        Vector3 n = Vector3.Cross(b - a, c - a);
                        if (n.sqrMagnitude < 1e-12f)
                        {
                            continue;
                        }
                        n.Normalize();

                        for (int k = 0; k < 3; k++)
                        {
                            int corner = k == 0 ? 0 : (k == 1 ? i : i + 1);
                            int pi = face[corner];
                            int ti = faceUV[corner];
                            outPos.Add(pos[pi]);
                            outNormal.Add(n);
                            outColor.Add(hasVertColor[pi] ? vertColor[pi] : mat.color);
                            outTint.Add(mat.tinted);
                            outUV.Add(ti >= 0 ? tex[ti] : Vector2.zero);
                            outMaterial.Add(current);
                        }
                    }
                }
            }

            if (outPos.Count == 0)
            {
                ModLog.Warn("[IsoRim] Model has no faces: " + path);
                return null;
            }

            Model m = new Model();
            m.positions = outPos.ToArray();
            m.normals = outNormal.ToArray();
            m.colors = outColor.ToArray();
            m.tinted = outTint.ToArray();
            m.uvs = outUV.ToArray();
            m.material = outMaterial.ToArray();
            m.materials = materials.ToArray();
            float maxY = 0f;
            for (int i = 0; i < m.positions.Length; i++)
            {
                maxY = Mathf.Max(maxY, m.positions[i].y);
            }
            m.maxY = maxY;
            float depth = 0f;
            for (int i = 0; i < m.positions.Length; i++)
            {
                depth = Mathf.Max(depth, Mathf.Abs(m.positions[i].z));
            }
            m.halfDepth = depth;
            m.minX = float.MaxValue;
            m.minZ = float.MaxValue;
            m.maxX = float.MinValue;
            m.maxZ = float.MinValue;
            for (int i = 0; i < m.positions.Length; i++)
            {
                Vector3 p = m.positions[i];
                m.minX = Mathf.Min(m.minX, p.x);
                m.maxX = Mathf.Max(m.maxX, p.x);
                m.minZ = Mathf.Min(m.minZ, p.z);
                m.maxZ = Mathf.Max(m.maxZ, p.z);
            }
            m.id = nextId++;
            m.hull = BuildHull(m.positions, m.normals, OutlineWidth);
            return m;
        }

        // Turns a 1-based OBJ index (negative counts back from the end) into a list index, or -1.
        private static int Index(string token, int count)
        {
            int idx;
            if (token.Length == 0 || !int.TryParse(token, NumberStyles.Integer, CultureInfo.InvariantCulture, out idx))
            {
                return -1;
            }
            idx = idx < 0 ? count + idx : idx - 1;
            return idx >= 0 && idx < count ? idx : -1;
        }

        private static int AddMaterial(string name, List<ModelMaterial> materials, Dictionary<string, int> materialIndex)
        {
            ModelMaterial mat = new ModelMaterial();
            mat.name = name;
            mat.tinted = name.StartsWith("stuff", StringComparison.OrdinalIgnoreCase);
            mat.leaf = name.StartsWith("leaf", StringComparison.OrdinalIgnoreCase);
            mat.twig = name.StartsWith("twig", StringComparison.OrdinalIgnoreCase);
            mat.glow = name.StartsWith("flame", StringComparison.OrdinalIgnoreCase) || name.StartsWith("glow", StringComparison.OrdinalIgnoreCase)
                || name.StartsWith("ember", StringComparison.OrdinalIgnoreCase);
            mat.color = mat.tinted ? Color.white : DefaultColor;
            materials.Add(mat);
            materialIndex[name] = materials.Count - 1;
            return materials.Count - 1;
        }

        // For the outline, each corner moves away from all the faces that meet there. Corners
        // that share a position move together, so the enlarged copy stays closed.
        private static Vector3[] BuildHull(Vector3[] positions, Vector3[] normals, float width)
        {
            Dictionary<Vector3Int, List<Vector3>> facesAt = new Dictionary<Vector3Int, List<Vector3>>();
            for (int i = 0; i < positions.Length; i++)
            {
                Vector3Int key = HullKey(positions[i]);
                List<Vector3> list;
                if (!facesAt.TryGetValue(key, out list))
                {
                    list = new List<Vector3>();
                    facesAt[key] = list;
                }
                bool known = false;
                for (int k = 0; k < list.Count; k++)
                {
                    if (Vector3.Dot(list[k], normals[i]) > 0.999f)
                    {
                        known = true;
                        break;
                    }
                }
                if (!known)
                {
                    list.Add(normals[i]);
                }
            }

            Vector3[] hull = new Vector3[positions.Length];
            for (int i = 0; i < positions.Length; i++)
            {
                List<Vector3> list = facesAt[HullKey(positions[i])];
                Vector3 sum = Vector3.zero;
                for (int k = 0; k < list.Count; k++)
                {
                    sum += list[k];
                }
                if (positions[i].y < 0.001f)
                {
                    sum.y = 0f;   // corners on the ground only move sideways
                }
                if (sum.sqrMagnitude < 1e-8f)
                {
                    hull[i] = Vector3.zero;
                    continue;
                }

                Vector3 dir = sum.normalized;
                float least = 1f;
                for (int k = 0; k < list.Count; k++)
                {
                    least = Mathf.Min(least, Vector3.Dot(dir, list[k]));
                }
                hull[i] = dir * (width / Mathf.Clamp(least, 0.4f, 1f));
            }
            return hull;
        }

        private static Vector3Int HullKey(Vector3 p)
        {
            return new Vector3Int(Mathf.RoundToInt(p.x * 10000f), Mathf.RoundToInt(p.y * 10000f), Mathf.RoundToInt(p.z * 10000f));
        }

        private static void ReadMaterials(string path, List<ModelMaterial> materials, Dictionary<string, int> materialIndex)
        {
            if (!File.Exists(path))
            {
                ModLog.Warn("[IsoRim] Material file not found: " + path);
                return;
            }
            ModelMaterial current = null;
            foreach (string raw in File.ReadAllLines(path))
            {
                string line = raw.Trim();
                if (line.Length == 0 || line[0] == '#')
                {
                    continue;
                }
                string[] t = line.Split(Separators, StringSplitOptions.RemoveEmptyEntries);
                if (t[0] == "newmtl" && t.Length > 1)
                {
                    int index;
                    if (!materialIndex.TryGetValue(t[1], out index))
                    {
                        index = AddMaterial(t[1], materials, materialIndex);
                    }
                    current = materials[index];
                }
                else if (t[0] == "Kd" && t.Length >= 4 && current != null)
                {
                    current.color = new Color(Num(t[1]), Num(t[2]), Num(t[3]));
                }
                else if (t[0] == "map_Kd" && t.Length >= 2 && current != null)
                {
                    current.texture = TexturePath(line.Substring(6).Trim());
                }
            }
        }

        // Accepts either a game content path (IsoRim/Swatches/Wood) or a file path that Blender
        // wrote (C:\...\Textures\IsoRim\Swatches\Wood.png) and returns the content path.
        private static string TexturePath(string value)
        {
            string p = value.Replace('\\', '/');
            int cut = p.LastIndexOf("Textures/", StringComparison.OrdinalIgnoreCase);
            if (cut >= 0)
            {
                p = p.Substring(cut + 9);
            }
            int dot = p.LastIndexOf('.');
            if (dot > p.LastIndexOf('/'))
            {
                p = p.Substring(0, dot);
            }
            p = p.Trim().TrimStart('/');
            return p.Length == 0 ? null : p;
        }

        private static float Num(string s)
        {
            float f;
            return float.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out f) ? f : 0f;
        }
    }

    // The mod's own textures, from its Textures folder. They are drawn with the same shader the
    // game uses for its sprites, with the colour (build material and shading) set per material.
    public static class R3DTextures
    {
        private static readonly Dictionary<string, Texture2D> cache = new Dictionary<string, Texture2D>();

        public static Texture2D Get(string path)
        {
            Texture2D tex;
            if (cache.TryGetValue(path, out tex))
            {
                return tex;
            }
            tex = ContentFinder<Texture2D>.Get(path, false);
            if (tex != null)
            {
                tex.wrapMode = TextureWrapMode.Repeat;   // the textures are made to tile
                // Smoothly filtered at a slant and at a distance, so fine patterns do not
                // shimmer as the camera moves.
                tex.filterMode = FilterMode.Trilinear;
                tex.anisoLevel = 4;
            }
            else
            {
                ModLog.Warn("[IsoRim] Texture not found: " + path);
            }
            cache[path] = tex;
            return tex;
        }

        // A material showing this texture multiplied by a colour, or null if the texture is missing.
        public static Material MaterialFor(string path, Color color)
        {
            if (Get(path) == null)
            {
                return null;
            }
            color.a = 1f;
            return MaterialPool.MatFrom(path, ShaderDatabase.Cutout, color);
        }

        public static int SwatchIndex(string swatch)
        {
            switch (swatch)
            {
                case "Stone":
                    return 1;
                case "Metal":
                    return 2;
                case "Fabric":
                    return 3;
                default:
                    return 0;
            }
        }

        // Which of the mod's surface textures matches what a thing is built from.
        public static string StuffSwatch(Thing t)
        {
            ThingDef stuff = t.Stuff;
            if (stuff == null || stuff.stuffProps == null)
            {
                return "Wood";
            }
            string name = stuff.stuffProps.appearance != null ? stuff.stuffProps.appearance.defName : "";
            if (name == "Bricks")
            {
                return "Stone";
            }
            if (name == "Smooth")
            {
                return "Metal";
            }
            if (name == "Planks")
            {
                return "Wood";
            }
            if (stuff.stuffProps.categories != null)
            {
                for (int i = 0; i < stuff.stuffProps.categories.Count; i++)
                {
                    string cat = stuff.stuffProps.categories[i].defName;
                    if (cat == "Stony")
                    {
                        return "Stone";
                    }
                    if (cat == "Metallic")
                    {
                        return "Metal";
                    }
                    if (cat == "Fabric" || cat == "Leathery")
                    {
                        return "Fabric";
                    }
                }
            }
            return "Wood";
        }
    }

    // The average colour of a thing's own sprite, used to colour the stand-in model of a plant
    // the mod has no model for, so it still looks like that plant from a distance.
    public static class SpriteColors
    {
        private const int N = 16;
        private static readonly Color Fallback = new Color(0.40f, 0.55f, 0.26f);
        private static readonly Dictionary<int, Color> cache = new Dictionary<int, Color>();

        public static Color MeanFor(Thing t)
        {
            try
            {
                Graphic g = t.Graphic;
                Material mat = g != null ? g.MatSingleFor(t) : null;
                if (mat == null || !mat.HasProperty("_MainTex") || mat.mainTexture == null)
                {
                    return Fallback;
                }
                Texture tex = mat.mainTexture;
                Color c;
                if (!cache.TryGetValue(tex.GetInstanceID(), out c))
                {
                    c = Read(tex);
                    cache[tex.GetInstanceID()] = c;
                }
                if (mat.HasProperty("_Color"))
                {
                    c *= mat.color;
                }
                c.a = 1f;
                return c;
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Reading a sprite's colour failed: " + e, 93611040);
                return Fallback;
            }
        }

        // Game textures cannot be read directly, so the sprite is drawn into a tiny off-screen
        // image first and that is read back.
        private static Color Read(Texture tex)
        {
            RenderTexture target = RenderTexture.GetTemporary(N, N, 0, RenderTextureFormat.ARGB32);
            RenderTexture previous = RenderTexture.active;
            Texture2D read = null;
            Color32[] px = null;
            try
            {
                Graphics.Blit(tex, target);
                RenderTexture.active = target;
                read = new Texture2D(N, N, TextureFormat.RGBA32, false);
                read.ReadPixels(new Rect(0f, 0f, N, N), 0, 0);
                read.Apply();
                px = read.GetPixels32();
            }
            finally
            {
                RenderTexture.active = previous;
                RenderTexture.ReleaseTemporary(target);
                if (read != null)
                {
                    UnityEngine.Object.Destroy(read);
                }
            }

            float r = 0f;
            float g = 0f;
            float b = 0f;
            int count = 0;
            if (px != null)
            {
                for (int i = 0; i < px.Length; i++)
                {
                    if (px[i].a >= 128)
                    {
                        r += px[i].r;
                        g += px[i].g;
                        b += px[i].b;
                        count++;
                    }
                }
            }
            if (count == 0)
            {
                return Fallback;
            }

            // The average includes the sprite's dark outlines, so lift it back up a little.
            Color mean = new Color(r / count / 255f, g / count / 255f, b / count / 255f, 1f);
            float brightest = Mathf.Max(mean.r, Mathf.Max(mean.g, mean.b));
            float lift = brightest > 0.01f ? Mathf.Clamp(0.62f / brightest, 1f, 1.6f) : 1f;
            return new Color(Mathf.Min(1f, mean.r * lift), Mathf.Min(1f, mean.g * lift), Mathf.Min(1f, mean.b * lift), 1f);
        }
    }

    // One shared material for all solid 3D geometry. It reads its colour from the vertices,
    // so shading and stuff colour are baked into the mesh and no custom shader is needed.
    [StaticConstructorOnStartup]
    public static class R3DMaterials
    {
        private static bool tried;
        private static Material solid;
        private static Material outline;
        private static bool shadowTried;
        private static Material gameShadow;
        private static Material plainShadow;
        private static bool groundShadowTried;
        private static Material groundShadow;

        // Light comes from above and from the south-west, so the faces turned toward the camera are lit.
        private static readonly Vector3 BaseLight = new Vector3(-0.35f, 0.8f, -0.5f).normalized;
        private static Vector3 LightDir = BaseLight;
        private static Vector2 LightFlat = new Vector2(BaseLight.x, BaseLight.z).normalized;
        private static int lightStep;

        // Things that move (people, animals, doors) have their shading worked into ready-made
        // meshes; those meshes are remade when this number changes, once per game hour of
        // sunlight (and once for the night). Everything that stays put is lit smoothly instead:
        // see Lit and LitTexture.
        public static int LightStep
        {
            get { return lightStep; }
        }

        // The direction moving things are shaded for: the sun as it was when the step last changed.
        private static Vector3 StepLightDir = BaseLight;
        private static float litHour = -100f;
        private static bool lightSet;

        // Where the sun is at a given hour: up in the east at six, high in the south at noon,
        // down in the west at six in the evening, and a fixed moonlight through the night, with
        // an hour's blend at dusk and dawn.
        public static Vector3 SunDirAt(float hour)
        {
            Vector3 moon = Dir(200f, 55f);
            if (hour >= 6f && hour <= 18f)
            {
                float t = (hour - 6f) / 12f;
                return Dir(95f + 170f * t, 22f + 40f * Mathf.Sin(t * Mathf.PI));
            }
            float k;
            Vector3 edge;
            if (hour > 18f)
            {
                k = Mathf.Clamp01(hour - 18f);
                edge = Dir(265f, 22f);
            }
            else
            {
                k = Mathf.Clamp01(6f - hour);
                edge = Dir(95f, 22f);
            }
            return Vector3.Slerp(edge, moon, k).normalized;
        }

        private static Vector3 Dir(float azimuth, float elevation)
        {
            float az = azimuth * Mathf.Deg2Rad;
            float el = elevation * Mathf.Deg2Rad;
            return new Vector3(Mathf.Sin(az) * Mathf.Cos(el), Mathf.Sin(el), Mathf.Cos(az) * Mathf.Cos(el)).normalized;
        }

        // Moves the sun to the given hour of the day. Cheap enough to call every frame: the lit
        // materials are only recoloured when the sun has moved on by about a game minute.
        public static void SetSunHour(float hour)
        {
            if (lightSet && Mathf.Abs(hour - litHour) < 0.02f)
            {
                return;
            }
            litHour = hour;
            lightSet = true;
            LightDir = SunDirAt(hour);
            LightFlat = new Vector2(LightDir.x, LightDir.z);
            if (LightFlat.sqrMagnitude < 1e-6f)
            {
                LightFlat = new Vector2(0f, -1f);
            }
            LightFlat.Normalize();
            int step = hour < 6f || hour >= 18f ? 99 : Mathf.FloorToInt(hour);
            if (step != lightStep)
            {
                lightStep = step;
                StepLightDir = LightDir;
            }
            RecolourLit();
        }

        // Kept so older code still compiles: a step of the old six-place sun, as an hour.
        public static void SetSun(int step)
        {
            SetSunHour(step >= 6 ? 0f : 6f + (step + 0.5f) * 2f);
        }

        // ---- smoothly lit materials
        //
        // Every face of the map's 3D geometry is sorted into one of these direction groups by
        // which way it faces: straight up, straight down, or one of eight compass points at
        // three steepnesses. All the faces in a group share a material whose colour is the
        // brightness the sun gives that direction right now, so as the sun moves every face
        // brightens and darkens smoothly without anything being rebuilt.
        public const int Bins = 26;
        private static readonly Vector3[] binNormal = MakeBinNormals();
        private static readonly Material[,] litSolid = new Material[2, Bins];
        private static readonly float[,] binShade = new float[2, Bins];

        private class LitEntry
        {
            public Material mat;
            public Color baseColor;
            public int bin;
            public int curve;
        }

        private static readonly List<LitEntry> litEntries = new List<LitEntry>();
        private static readonly Dictionary<string, Material> litByKey = new Dictionary<string, Material>();

        private static Vector3[] MakeBinNormals()
        {
            Vector3[] n = new Vector3[Bins];
            n[0] = Vector3.up;
            n[1] = Vector3.down;
            float[] elevations = { 0f, 35f, 62f };
            for (int band = 0; band < 3; band++)
            {
                for (int sector = 0; sector < 8; sector++)
                {
                    n[2 + band * 8 + sector] = Dir(sector * 45f, elevations[band]);
                }
            }
            return n;
        }

        // Which direction group a face pointing along normal belongs to.
        public static int BinOf(Vector3 normal)
        {
            float len = normal.magnitude;
            if (len < 1e-6f)
            {
                return 0;
            }
            normal /= len;
            if (normal.y >= 0.92f)
            {
                return 0;
            }
            if (normal.y <= -0.5f)
            {
                return 1;
            }
            int band = normal.y < 0.25f ? 0 : (normal.y < 0.65f ? 1 : 2);
            float az = Mathf.Atan2(normal.x, normal.z) * Mathf.Rad2Deg;
            int sector = Mathf.RoundToInt(Mathf.Repeat(az, 360f) / 45f) % 8;
            return 2 + band * 8 + sector;
        }

        // How bright faces of a group are now. curve 0 is for models, 1 for walls and rock,
        // which keep a narrower, steadier range (see WallShade).
        public static float BinShade(int bin, int curve)
        {
            if (!lightSet)
            {
                SetSunHour(10f);
            }
            return binShade[curve == 1 ? 1 : 0, Mathf.Clamp(bin, 0, Bins - 1)];
        }

        // The plain solid material for a direction group: vertex colours times the sun.
        public static Material Lit(int bin, int curve = 0)
        {
            if (Solid == null)
            {
                return null;
            }
            bin = Mathf.Clamp(bin, 0, Bins - 1);
            curve = curve == 1 ? 1 : 0;
            Material m = litSolid[curve, bin];
            if (m == null)
            {
                m = new Material(solid);
                m.name = "IsoRim_Lit_" + curve + "_" + bin;
                m.color = Grey(BinShade(bin, curve));
                litSolid[curve, bin] = m;
            }
            return m;
        }

        // A texture times a colour, lit for a direction group. Shared by every face with the
        // same texture, colour and direction. Null if the texture is missing.
        public static Material LitTexture(string path, Color baseColor, int bin, int curve = 0)
        {
            bin = Mathf.Clamp(bin, 0, Bins - 1);
            curve = curve == 1 ? 1 : 0;
            Color32 c = baseColor;
            string key = path + "|" + c.r + "," + c.g + "," + c.b + "|" + bin + "|" + curve;
            Material m;
            if (litByKey.TryGetValue(key, out m))
            {
                return m;
            }
            Texture2D tex = R3DTextures.Get(path);
            if (tex != null)
            {
                m = new Material(ShaderDatabase.Cutout);
                m.name = "IsoRim_LitTex_" + bin;
                m.mainTexture = tex;
                baseColor.a = 1f;
                LitEntry e = new LitEntry { mat = m, baseColor = baseColor, bin = bin, curve = curve };
                litEntries.Add(e);
                m.color = Tinted(e);
            }
            litByKey[key] = m;
            return m;
        }

        private static Color Grey(float v)
        {
            return new Color(v, v, v, 1f);
        }

        private static Color Tinted(LitEntry e)
        {
            float s = BinShade(e.bin, e.curve);
            return new Color(e.baseColor.r * s, e.baseColor.g * s, e.baseColor.b * s, 1f);
        }

        private static void RecolourLit()
        {
            for (int b = 0; b < Bins; b++)
            {
                Vector3 n = binNormal[b];
                binShade[0, b] = ModelShade(n, LightDir);
                binShade[1, b] = b == 0 ? 1f : WallShadeFor(n, LightFlat);
            }
            for (int curve = 0; curve < 2; curve++)
            {
                for (int b = 0; b < Bins; b++)
                {
                    if (litSolid[curve, b] != null)
                    {
                        litSolid[curve, b].color = Grey(binShade[curve, b]);
                    }
                }
            }
            for (int i = 0; i < litEntries.Count; i++)
            {
                LitEntry e = litEntries[i];
                if (e.mat != null)
                {
                    e.mat.color = Tinted(e);
                }
            }
        }

        private static float ModelShade(Vector3 normal, Vector3 light)
        {
            float d = Mathf.Max(0f, Vector3.Dot(normal, light));
            return 0.5f + 0.5f * Mathf.Clamp01(d / Mathf.Max(0.2f, light.y));
        }

        private static float WallShadeFor(Vector3 outward, Vector2 lightFlat)
        {
            Vector2 o = new Vector2(outward.x, outward.z);
            if (o.sqrMagnitude < 1e-6f)
            {
                return 1f;
            }
            float d = Vector2.Dot(o.normalized, lightFlat);
            return Mathf.Lerp(0.52f, 0.80f, (d + 1f) * 0.5f);
        }

        // Kept for older callers: the light no longer follows the camera.
        public static void FaceCamera(int step)
        {
        }

        // How bright an upright face is that looks out along the given direction on the ground:
        // 0.80 for the side facing the light, down to about 0.52 for the side facing away.
        public static float WallShade(Vector3 outward)
        {
            Vector2 o = new Vector2(outward.x, outward.z);
            if (o.sqrMagnitude < 1e-6f)
            {
                return 1f;
            }
            float d = Vector2.Dot(o.normalized, LightFlat);
            return Mathf.Lerp(0.52f, 0.80f, (d + 1f) * 0.5f);
        }

        public static Material Solid
        {
            get
            {
                if (!tried)
                {
                    Init();
                }
                return solid;
            }
        }

        // Same as Solid but drawn inside out: only the faces turned away from the camera show.
        public static Material Outline
        {
            get
            {
                if (!tried)
                {
                    Init();
                }
                return outline;
            }
        }

        private static void Init()
        {
            tried = true;

            // Built into every Unity player; draws plain vertex colours.
            Shader shader = Shader.Find("Hidden/Internal-Colored");
            if (shader == null)
            {
                FieldInfo f = AccessTools.Field(typeof(ShaderDatabase), "VertexColor");
                if (f != null)
                {
                    shader = f.GetValue(null) as Shader;
                }
            }
            if (shader == null)
            {
                Log.Error("[IsoRim] No vertex-colour shader is available, so walls and models cannot be drawn in 3D.");
                return;
            }

            solid = new Material(shader);
            solid.name = "IsoRim_Solid";
            solid.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.One);
            solid.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.Zero);
            solid.SetInt("_ZWrite", 1);
            solid.SetInt("_ZTest", (int)UnityEngine.Rendering.CompareFunction.LessEqual);
            solid.SetInt("_Cull", (int)UnityEngine.Rendering.CullMode.Off);
            solid.renderQueue = 2000;

            outline = new Material(solid);
            outline.name = "IsoRim_Outline";
            outline.SetInt("_Cull", (int)UnityEngine.Rendering.CullMode.Front);
            // Pushed back a touch in depth, so that where the outline shell runs close to the
            // model's own faces it can never show through them.
            outline.SetFloat("_ZBias", 1f);
        }

        // See-through, coloured from the vertices, for the ghosts of things still to be built.
        private static Material ghost;

        public static Material Ghost
        {
            get
            {
                if (ghost == null && Solid != null)
                {
                    ghost = new Material(solid);
                    ghost.name = "IsoRim_Ghost";
                    ghost.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
                    ghost.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                    ghost.SetInt("_ZWrite", 1);
                    ghost.SetInt("_Cull", (int)UnityEngine.Rendering.CullMode.Back);
                    ghost.renderQueue = 3100;
                }
                return ghost;
            }
        }

        // The solid material again, drawn late (after the night and indoor darkness) so that roofs
        // are not darkened by the rooms under them. Roofs dim with the daylight themselves.
        private static Material roof;

        public static Material Roof
        {
            get
            {
                if (roof == null && Solid != null)
                {
                    roof = new Material(solid);
                    roof.name = "IsoRim_Roof";
                    roof.renderQueue = 3600;
                }
                return roof;
            }
        }

        // See-through, coloured from the vertices, drawn after the ground and the game's own water,
        // so the water's moving shader shows through the mod's bands of colour and foam.
        private static Material waterOverlay;

        public static Material WaterOverlay
        {
            get
            {
                if (waterOverlay == null && Solid != null)
                {
                    waterOverlay = new Material(solid);
                    waterOverlay.name = "IsoRim_Water";
                    waterOverlay.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
                    waterOverlay.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                    waterOverlay.SetInt("_ZWrite", 0);
                    waterOverlay.renderQueue = 3050;
                }
                return waterOverlay;
            }
        }

        // The game's own shadow material. Whatever is drawn with it is slid along the ground by
        // the game according to the time of day, takes the game's shadow colour and fades out at
        // night, exactly like the shadows of walls and colonists. Null if the game has changed.
        public static Material GameShadow
        {
            get
            {
                if (!shadowTried)
                {
                    InitShadow();
                }
                return gameShadow;
            }
        }

        // A plain see-through black, used for shadows only when GameShadow is missing.
        public static Material PlainShadow
        {
            get
            {
                if (!shadowTried)
                {
                    InitShadow();
                }
                return plainShadow;
            }
        }

        // See-through black for the soft shading under things. How dark it is at each corner comes
        // from the corner's own colour, so one piece can fade from dark to nothing. It is drawn
        // straight after the ground, before anything that stands on it.
        public static Material GroundShadow
        {
            get
            {
                if (!groundShadowTried)
                {
                    groundShadowTried = true;
                    Material basis = Solid;
                    if (basis != null)
                    {
                        groundShadow = new Material(basis);
                        groundShadow.name = "IsoRim_GroundShadow";
                        groundShadow.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
                        groundShadow.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                        groundShadow.SetInt("_ZWrite", 0);
                        groundShadow.renderQueue = 2420;
                    }
                }
                return groundShadow;
            }
        }

        private static void InitShadow()
        {
            shadowTried = true;
            try
            {
                Type bases = AccessTools.TypeByName("Verse.MatBases");
                string[] names = { "SunShadowFade", "SunShadow" };
                for (int i = 0; i < names.Length && gameShadow == null && bases != null; i++)
                {
                    FieldInfo f = AccessTools.Field(bases, names[i]);
                    gameShadow = f != null ? f.GetValue(null) as Material : null;
                }
            }
            catch (Exception e)
            {
                gameShadow = null;
                ModLog.Warn("[IsoRim] Looking up the game's shadow material failed: " + e.Message);
            }
            if (gameShadow != null)
            {
                return;
            }

            ModLog.Warn("[IsoRim] The game's shadow material was not found, so tree shadows will not move with the sun.");
            Material basis = Solid;
            if (basis == null)
            {
                return;
            }
            plainShadow = new Material(basis);
            plainShadow.name = "IsoRim_Shadow";
            plainShadow.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            plainShadow.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            plainShadow.SetInt("_ZWrite", 0);
            plainShadow.renderQueue = 2900;
        }

        // Brightness for a face pointing along the given direction: 1 on top, 0.5 in full shade.
        // (Used for things that move, whose meshes are remade with each LightStep.)
        public static float Shade(Vector3 normal)
        {
            if (!lightSet)
            {
                SetSunHour(10f);
            }
            return ModelShade(normal, StepLightDir);
        }

        public static Color32 Shaded(Color c, float shade)
        {
            return new Color32(
                (byte)Mathf.Clamp(c.r * shade * 255f, 0f, 255f),
                (byte)Mathf.Clamp(c.g * shade * 255f, 0f, 255f),
                (byte)Mathf.Clamp(c.b * shade * 255f, 0f, 255f),
                255);
        }
    }
}
