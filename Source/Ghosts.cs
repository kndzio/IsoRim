using System;
using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;

namespace IsoRim
{
    // Things still to be built shown as see-through 3D ghosts of what they will become, in
    // place of the game's flat blue sprites: blueprints in blue, frames under construction in
    // pale sawdust, and the preview under the pointer while choosing where to build.
    public static class Ghosts
    {
        public static readonly Color BlueprintColor = new Color(0.42f, 0.70f, 1f, 0.42f);
        public static readonly Color FrameColor = new Color(0.96f, 0.86f, 0.64f, 0.46f);

        // What a blueprint or frame will become, or null.
        public static ThingDef Target(Thing t)
        {
            if (!(t is Blueprint) && !(t is Frame))
            {
                return null;
            }
            return t.def.entityDefToBuild as ThingDef;
        }

        // Writes the ghost of a blueprint or frame into a block of the map. Returns false if the
        // thing it will become has no 3D shape, so the game's own sprite should be drawn.
        public static bool Print(SectionLayer layer, Thing t)
        {
            IsoRimSettings st = IsoRimMod.Settings;
            ThingDef target = Target(t);
            if (!st.ghosts3D || target == null)
            {
                return false;
            }
            ThingForm form = Forms.For(target);
            Color col = t is Frame ? FrameColor : BlueprintColor;
            try
            {
                if (form.form == Form3D.Model && form.model != null)
                {
                    ModelBaker.Ghost = col;
                    try
                    {
                        return ModelBaker.Bake(layer, t, form.model, 0f);
                    }
                    finally
                    {
                        ModelBaker.Ghost = new Color(0f, 0f, 0f, 0f);
                    }
                }
                if (form.form == Form3D.Block)
                {
                    return Box(layer, t.Position, form.height, col);
                }
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Drawing a blueprint ghost failed: " + e, 93611130);
            }
            return false;
        }

        // A see-through block one cell across and height cells high, for walls still to be built.
        private static bool Box(SectionLayer layer, IntVec3 c, float height, Color col)
        {
            Material mat = R3DMaterials.Ghost;
            LayerSubMesh sm = mat != null ? MeshWriter.Sub(layer, mat) : null;
            if (sm == null || sm.verts.Count + 20 > MeshWriter.MaxVerts)
            {
                return false;
            }
            float y = height / View3D.Squash;
            float x0 = c.x + 0.02f;
            float z0 = c.z + 0.02f;
            float x1 = c.x + 0.98f;
            float z1 = c.z + 0.98f;
            Color32 top = col;
            Color32 side = new Color(col.r * 0.78f, col.g * 0.78f, col.b * 0.78f, col.a);
            MeshWriter.Quad(sm, new Vector3(x0, y, z0), new Vector3(x0, y, z1), new Vector3(x1, y, z1), new Vector3(x1, y, z0), top);
            MeshWriter.Quad(sm, new Vector3(x0, 0f, z0), new Vector3(x0, y, z0), new Vector3(x1, y, z0), new Vector3(x1, 0f, z0), side);
            MeshWriter.Quad(sm, new Vector3(x1, 0f, z1), new Vector3(x1, y, z1), new Vector3(x0, y, z1), new Vector3(x0, 0f, z1), side);
            MeshWriter.Quad(sm, new Vector3(x0, 0f, z1), new Vector3(x0, y, z1), new Vector3(x0, y, z0), new Vector3(x0, 0f, z0), side);
            MeshWriter.Quad(sm, new Vector3(x1, 0f, z0), new Vector3(x1, y, z0), new Vector3(x1, y, z1), new Vector3(x1, 0f, z1), side);
            return true;
        }

        // ---- the preview under the pointer, drawn every frame

        private static readonly Dictionary<int, Mesh> meshes = new Dictionary<int, Mesh>();
        private static Mesh unitBox;

        // def: what is being placed; center: its cell; rot: its rotation. tint: the game's
        // ghost colour (green where it can go, red where it cannot).
        public static void DrawPreview(ThingDef def, IntVec3 center, Rot4 rot, Color tint)
        {
            IsoRimSettings st = IsoRimMod.Settings;
            Material mat = R3DMaterials.Ghost;
            if (!st.ghosts3D || def == null || mat == null)
            {
                return;
            }
            ThingForm form = Forms.For(def);
            float s = View3D.Squash;
            Color col = new Color(Mathf.Lerp(tint.r, 0.6f, 0.25f), Mathf.Lerp(tint.g, 0.8f, 0.25f), Mathf.Lerp(tint.b, 1f, 0.25f), 0.45f);
            if (form.form == Form3D.Model && form.model != null && form.model.HasModel)
            {
                ModelEntry entry = form.model;
                Model m = entry.variants[0];
                Mesh mesh = MeshFor(m);
                if (mesh == null)
                {
                    return;
                }
                Vector3 at = GenThing.TrueCenter(center, rot, def.size, 0f);
                float yaw = rot.AsAngle + entry.def.rotation;
                if (entry.Swapped(def))
                {
                    yaw += 90f;
                }
                Vector3 fit = entry.Fit(def) * entry.def.scale;
                Quaternion turn = Quaternion.AngleAxis(yaw, Vector3.up);
                Vector3 offset = turn * Vector3.Scale(entry.def.offset, Vector3.one);
                Matrix4x4 matrix = Matrix4x4.Translate(new Vector3(at.x + offset.x, offset.y / s, at.z + offset.z))
                    * Matrix4x4.Scale(new Vector3(1f, 1f / s, 1f))
                    * Matrix4x4.Rotate(turn)
                    * Matrix4x4.Scale(fit);
                Draw(mesh, matrix, col);
            }
            else if (form.form == Form3D.Block)
            {
                if (unitBox == null)
                {
                    unitBox = MakeBox();
                }
                Matrix4x4 matrix = Matrix4x4.Translate(new Vector3(center.x + 0.5f, 0f, center.z + 0.5f))
                    * Matrix4x4.Scale(new Vector3(0.96f, form.height / s, 0.96f));
                Draw(unitBox, matrix, col);
            }
        }

        private static MaterialPropertyBlock block;
        private static int colorId;

        private static void Draw(Mesh mesh, Matrix4x4 matrix, Color col)
        {
            if (block == null)
            {
                block = new MaterialPropertyBlock();
                colorId = Shader.PropertyToID("_Color");
            }
            block.SetColor(colorId, col);
            Graphics.DrawMesh(mesh, matrix, R3DMaterials.Ghost, 0, null, 0, block);
        }

        // The model as one white mesh, shaded a little by which way each face looks; the
        // colour comes from the material when it is drawn.
        private static Mesh MeshFor(Model m)
        {
            Mesh mesh;
            if (meshes.TryGetValue(m.id, out mesh))
            {
                return mesh;
            }
            List<Vector3> v = new List<Vector3>();
            List<Color32> c = new List<Color32>();
            List<int> t = new List<int>();
            for (int i = 0; i + 2 < m.positions.Length; i += 3)
            {
                float k = 0.70f + 0.30f * Mathf.Clamp01(m.normals[i].y * 0.5f + 0.5f);
                Color32 shade = new Color(k, k, k, 1f);
                for (int j = i; j < i + 3; j++)
                {
                    t.Add(v.Count);
                    Vector3 p = m.positions[j];
                    v.Add(new Vector3(p.x, Mathf.Max(0f, p.y), p.z));
                    c.Add(shade);
                }
            }
            mesh = new Mesh();
            if (v.Count > 65000)
            {
                mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
            }
            mesh.SetVertices(v);
            mesh.SetColors(c);
            mesh.SetTriangles(t, 0);
            mesh.RecalculateBounds();
            meshes[m.id] = mesh;
            return mesh;
        }

        // A box one unit across and one high, standing on the ground, centred on the origin.
        private static Mesh MakeBox()
        {
            List<Vector3> v = new List<Vector3>();
            List<Color32> c = new List<Color32>();
            List<int> t = new List<int>();
            Color32 top = new Color32(255, 255, 255, 255);
            Color32 side = new Color32(200, 200, 200, 255);
            Vector3[] q =
            {
                new Vector3(-0.5f, 1f, -0.5f), new Vector3(-0.5f, 1f, 0.5f), new Vector3(0.5f, 1f, 0.5f), new Vector3(0.5f, 1f, -0.5f),
                new Vector3(-0.5f, 0f, -0.5f), new Vector3(-0.5f, 1f, -0.5f), new Vector3(0.5f, 1f, -0.5f), new Vector3(0.5f, 0f, -0.5f),
                new Vector3(0.5f, 0f, 0.5f), new Vector3(0.5f, 1f, 0.5f), new Vector3(-0.5f, 1f, 0.5f), new Vector3(-0.5f, 0f, 0.5f),
                new Vector3(-0.5f, 0f, 0.5f), new Vector3(-0.5f, 1f, 0.5f), new Vector3(-0.5f, 1f, -0.5f), new Vector3(-0.5f, 0f, -0.5f),
                new Vector3(0.5f, 0f, -0.5f), new Vector3(0.5f, 1f, -0.5f), new Vector3(0.5f, 1f, 0.5f), new Vector3(0.5f, 0f, 0.5f),
            };
            for (int f = 0; f < 5; f++)
            {
                int b = v.Count;
                for (int k = 0; k < 4; k++)
                {
                    v.Add(q[f * 4 + k]);
                    c.Add(f == 0 ? top : side);
                }
                // Both windings, so the box shows whichever way the camera's view turns its faces.
                t.AddRange(new[] { b, b + 1, b + 2, b, b + 2, b + 3, b, b + 2, b + 1, b, b + 3, b + 2 });
            }
            Mesh mesh = new Mesh();
            mesh.SetVertices(v);
            mesh.SetColors(c);
            mesh.SetTriangles(t, 0);
            mesh.RecalculateBounds();
            return mesh;
        }
    }
}
