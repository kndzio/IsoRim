using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;

namespace IsoRim
{
    // Stand-ins for UnityEngine.Graphics.DrawMesh. The pawn drawing code is rewritten (see
    // Patches.RedirectDrawCalls) to call these instead. While "active" is set, every mesh drawn
    // has "xform" applied on top of its own transform; otherwise they behave exactly like the
    // originals. Each method must keep the same parameter list as the overload it replaces.
    public static class DrawHook
    {
        public static bool active;
        public static Matrix4x4 xform = Matrix4x4.identity;

        // While set (with active), each mesh is instead stood upright where it is, facing the
        // camera, and raised by billboardHeight cells: status icons, bubbles and designations
        // float above things instead of lying on the floor.
        public static bool billboard;
        public static float billboardHeight;

        // With an anchor, icons are pulled in over the anchor (the middle of the thing they
        // belong to), keeping only their spread across the screen, so a thing's icons hang
        // in a row over it, like the diamond over a Sim's head.
        public static bool hasAnchor;
        public static Vector3 billboardAnchor;

        // How far flat overlays (field edges, drag highlights, placement sprites) are kept off
        // the ground: the game spaces its drawing layers far apart in height, which the 3D view
        // would otherwise show as overlays floating in the air.
        private const float FlatKeep = 0.08f;

        public static Matrix4x4 Flatten(Matrix4x4 matrix)
        {
            return Matrix4x4.Scale(new Vector3(1f, FlatKeep, 1f)) * matrix;
        }

        // The transform to draw a mesh with while active.
        public static Matrix4x4 Transform(Matrix4x4 matrix)
        {
            if (!billboard)
            {
                return xform * matrix;
            }
            Vector3 p = matrix.GetColumn(3);
            Matrix4x4 local = Matrix4x4.Translate(-p) * matrix;
            if (hasAnchor)
            {
                Vector3 right = Quaternion.Euler(0f, View3D.Yaw, 0f) * Vector3.right;
                float along = Vector3.Dot(new Vector3(p.x - billboardAnchor.x, 0f, p.z - billboardAnchor.z), right);
                p = new Vector3(billboardAnchor.x + right.x * along, p.y, billboardAnchor.z + right.z * along);
            }
            float s = View3D.Squash;
            return Matrix4x4.Translate(new Vector3(p.x, p.y + billboardHeight / s, p.z))
                * Matrix4x4.Scale(new Vector3(1f, 1f / s, 1f))
                * Matrix4x4.Rotate(Quaternion.Euler(View3D.Pitch - 90f, View3D.Yaw, 0f))
                * local;
        }

        // While set, nothing is drawn at all: a 3D model is standing in for the sprite.
        public static bool skip;

        private static readonly Dictionary<MethodInfo, MethodInfo> replacements = new Dictionary<MethodInfo, MethodInfo>();

        public static void DrawMesh(Mesh mesh, Matrix4x4 matrix, Material material, int layer)
        {
            if (skip)
            {
                return;
            }
            if (active)
            {
                matrix = Transform(matrix);
            }

            Graphics.DrawMesh(mesh, matrix, material, layer);
        }

        public static void DrawMesh(Mesh mesh, Vector3 position, Quaternion rotation, Material material, int layer)
        {
            if (skip)
            {
                return;
            }
            if (active)
            {
                Graphics.DrawMesh(mesh, Transform(Matrix4x4.TRS(position, rotation, Vector3.one)), material, layer);
            }

            else
            {
                Graphics.DrawMesh(mesh, position, rotation, material, layer);
            }
        }

        public static void DrawMesh(Mesh mesh, Matrix4x4 matrix, Material material, int layer, Camera camera, int submeshIndex, MaterialPropertyBlock properties)
        {
            if (skip)
            {
                return;
            }
            if (active)
            {
                matrix = Transform(matrix);
            }

            Graphics.DrawMesh(mesh, matrix, material, layer, camera, submeshIndex, properties);
        }

        public static void DrawMesh(Mesh mesh, Vector3 position, Quaternion rotation, Material material, int layer, Camera camera, int submeshIndex, MaterialPropertyBlock properties)
        {
            if (skip)
            {
                return;
            }
            if (active)
            {
                Graphics.DrawMesh(mesh, Transform(Matrix4x4.TRS(position, rotation, Vector3.one)), material, layer, camera, submeshIndex, properties);
            }

            else
            {
                Graphics.DrawMesh(mesh, position, rotation, material, layer, camera, submeshIndex, properties);
            }
        }

        // The stand-in with the same parameter list as the given Graphics.DrawMesh overload, or null.
        public static MethodInfo ReplacementFor(MethodInfo original)
        {
            MethodInfo found;
            if (replacements.TryGetValue(original, out found))
            {
                return found;
            }

            ParameterInfo[] ps = original.GetParameters();
            Type[] types = new Type[ps.Length];
            for (int i = 0; i < ps.Length; i++)
            {
                types[i] = ps[i].ParameterType;
            }
            found = typeof(DrawHook).GetMethod("DrawMesh", BindingFlags.Public | BindingFlags.Static, null, types, null);
            replacements[original] = found;
            return found;
        }
    }
}
