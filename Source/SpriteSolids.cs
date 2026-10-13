using System;
using System.Collections.Generic;
using UnityEngine;
using Verse;

namespace IsoRim
{
    // Weapons held by 3D figures, made from the weapon's own game sprite so they look exactly
    // like the game's: the sprite is shown on both faces of a thin slab, and the edges between
    // the faces are filled in with the colours of the sprite's own outline, like the items on
    // the ground. The slab stands on edge in the figure's hands and points where they aim.
    public static class SpriteSolids
    {
        private const float Thickness = 0.05f;   // cells
        private const float Size = 0.8f;         // of the weapon's drawn size, to suit the figures

        private class Solid
        {
            public Mesh faces;
            public Mesh sides;
        }

        private static readonly Dictionary<int, Solid> cache = new Dictionary<int, Solid>();

        // hand: x and z in map cells, y the height above the ground in cells. aim: the direction
        // it points, in degrees clockwise from north. Returns false if the sprite could not be
        // used, so that the caller can fall back to something else.
        public static bool DrawHeld(Thing weapon, Vector3 hand, float aim)
        {
            Graphic g = weapon.Graphic;
            Material mat = g != null ? g.MatSingleFor(weapon) : null;
            Material sideMat = R3DMaterials.Solid;
            if (mat == null || sideMat == null || !mat.HasProperty("_MainTex") || mat.mainTexture == null)
            {
                return false;
            }
            Solid solid = For(mat);
            if (solid == null)
            {
                return false;
            }

            Vector2 draw = g.drawSize;
            float s = View3D.Squash;
            Matrix4x4 m = Matrix4x4.Translate(new Vector3(hand.x, hand.y / s, hand.z))
                * Matrix4x4.Scale(new Vector3(1f, 1f / s, 1f))
                * Matrix4x4.Rotate(Quaternion.AngleAxis(aim - 90f, Vector3.up))
                // The game turns some sprites (swords, spears) by a set angle to hold them;
                // turning the other way first lines the weapon up with where it points.
                * Matrix4x4.Rotate(Quaternion.AngleAxis(-weapon.def.equippedAngleOffset, Vector3.forward))
                * Matrix4x4.Scale(new Vector3(draw.x * Size, draw.y * Size, 1f));
            Graphics.DrawMesh(solid.sides, m, sideMat, 0);
            Graphics.DrawMesh(solid.faces, m, mat, 0);
            return true;
        }

        private static Solid For(Material mat)
        {
            int key = mat.GetInstanceID();
            Solid solid;
            if (cache.TryGetValue(key, out solid))
            {
                return solid;
            }
            try
            {
                solid = Build(mat);
            }
            catch (Exception e)
            {
                solid = null;
                Log.ErrorOnce("[IsoRim] Making a held weapon from its sprite failed: " + e, 93611120);
            }
            cache[key] = solid;
            return solid;
        }

        // The slab one unit square (the drawn size is applied when it is drawn), centred on the
        // origin, the sprite across X (along) and Y (up), thickness along Z.
        private static Solid Build(Material mat)
        {
            Extruder.Mask mask = Extruder.MaskOf(mat.mainTexture, Vector2.one, Vector2.zero);
            if (mask == null)
            {
                return null;
            }
            float h = Thickness * 0.5f;

            // Both faces, each wound both ways so it shows whatever the sprite shader culls.
            List<Vector3> fv = new List<Vector3>();
            List<Vector2> fuv = new List<Vector2>();
            List<int> ft = new List<int>();
            for (int side = -1; side <= 1; side += 2)
            {
                int b = fv.Count;
                fv.Add(new Vector3(-0.5f, -0.5f, side * h));
                fv.Add(new Vector3(-0.5f, 0.5f, side * h));
                fv.Add(new Vector3(0.5f, 0.5f, side * h));
                fv.Add(new Vector3(0.5f, -0.5f, side * h));
                fuv.Add(new Vector2(0f, 0f));
                fuv.Add(new Vector2(0f, 1f));
                fuv.Add(new Vector2(1f, 1f));
                fuv.Add(new Vector2(1f, 0f));
                ft.AddRange(new[] { b, b + 1, b + 2, b, b + 2, b + 3, b, b + 2, b + 1, b, b + 3, b + 2 });
            }
            Mesh faces = new Mesh();
            faces.SetVertices(fv);
            faces.SetUVs(0, fuv);
            List<Color32> fc = new List<Color32>();
            for (int i = 0; i < fv.Count; i++)
            {
                fc.Add(new Color32(255, 255, 255, 255));   // some sprite shaders multiply by the vertex colour
            }
            faces.SetColors(fc);
            faces.SetTriangles(ft, 0);
            faces.RecalculateBounds();

            // The edges, coloured from the sprite just inside each one: lit from above, darker below.
            Color tint = mat.HasProperty("_Color") ? mat.color : Color.white;
            List<Vector3> sv = new List<Vector3>();
            List<Color32> sc = new List<Color32>();
            List<int> st = new List<int>();
            for (int i = 0; i < mask.runs.Count; i++)
            {
                Extruder.Run r = mask.runs[i];
                float shade = r.dir == 1 ? 1f : (r.dir == 0 ? 0.6f : (r.dir == 2 ? 0.78f : 0.86f));
                Color32 c0 = R3DMaterials.Shaded(r.c0 * tint, shade);
                Color32 c1 = R3DMaterials.Shaded(r.c1 * tint, shade);
                Vector3 p = new Vector3(r.a0 - 0.5f, r.b0 - 0.5f, 0f);
                Vector3 q = new Vector3(r.a1 - 0.5f, r.b1 - 0.5f, 0f);
                int b = sv.Count;
                sv.Add(new Vector3(p.x, p.y, -h));
                sv.Add(new Vector3(p.x, p.y, h));
                sv.Add(new Vector3(q.x, q.y, h));
                sv.Add(new Vector3(q.x, q.y, -h));
                sc.Add(c0);
                sc.Add(c0);
                sc.Add(c1);
                sc.Add(c1);
                st.AddRange(new[] { b, b + 1, b + 2, b, b + 2, b + 3 });
            }
            // A plain fill between the faces, so the slab looks solid from any angle even where
            // the sprite is see-through at its very edge.
            Color32 fill = R3DMaterials.Shaded(mask.mean * tint, 0.7f);
            for (int i = 0; i < mask.lids.Count; i++)
            {
                Vector4 l = mask.lids[i];
                for (int side = -1; side <= 1; side += 2)
                {
                    float z = side * h * 0.8f;
                    int b = sv.Count;
                    sv.Add(new Vector3(l.x - 0.5f, l.y - 0.5f, z));
                    sv.Add(new Vector3(l.x - 0.5f, l.w - 0.5f, z));
                    sv.Add(new Vector3(l.z - 0.5f, l.w - 0.5f, z));
                    sv.Add(new Vector3(l.z - 0.5f, l.y - 0.5f, z));
                    for (int k = 0; k < 4; k++)
                    {
                        sc.Add(fill);
                    }
                    st.AddRange(new[] { b, b + 1, b + 2, b, b + 2, b + 3 });
                }
            }
            Mesh sides = new Mesh();
            if (sv.Count > 65000)
            {
                sides.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
            }
            sides.SetVertices(sv);
            sides.SetColors(sc);
            sides.SetTriangles(st, 0);
            sides.RecalculateBounds();

            Solid solid = new Solid();
            solid.faces = faces;
            solid.sides = sides;
            return solid;
        }
    }
}
