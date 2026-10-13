using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;
using Verse;

namespace IsoRim
{
    // Redraws one layer of the map's 17 x 17 blocks a few at a time instead of the whole map at once,
    // the blocks on screen first. Used to relight the map after the camera turns and to build or drop
    // the roofs when they are switched on or off, without a long pause.
    public static class MapSections
    {
        private struct Job
        {
            public Map map;
            public object section;
            public Type layer;
        }

        private const int SectionSize = 17;

        private static readonly List<Job> queue = new List<Job>();
        private static int head;
        private static bool looked;
        private static FieldInfo sectionsField;
        private static MethodInfo getLayer;
        private static Type thingsLayer;

        public static Type ThingsLayer
        {
            get
            {
                Look();
                return thingsLayer;
            }
        }

        private static void Look()
        {
            if (looked)
            {
                return;
            }
            looked = true;
            sectionsField = AccessTools.Field(typeof(MapDrawer), "sections");
            Type section = AccessTools.TypeByName("Verse.Section");
            getLayer = section != null ? AccessTools.Method(section, "GetLayer", new[] { typeof(Type) }) : null;
            thingsLayer = AccessTools.TypeByName("Verse.SectionLayer_ThingsGeneral");
            if (sectionsField == null || getLayer == null)
            {
                ModLog.Warn("[IsoRim] The game's map blocks were not found in the expected form; the whole map is redrawn at once instead.");
            }
        }

        // Tells the game which kinds of change (terrain, roofs, buildings ...) make a layer redraw.
        // The game's type for these has changed between versions (a set of flags, or one def per
        // kind of change), so the values are looked up by name and combined whatever form they take.
        public static void SetChangeFlags(SectionLayer layer, params string[] names)
        {
            try
            {
                FieldInfo field = AccessTools.Field(typeof(SectionLayer), "relevantChangeTypes");
                if (field == null)
                {
                    return;
                }
                Type type = field.FieldType;
                Type defOf = AccessTools.TypeByName("Verse.MapMeshFlagDefOf");
                ulong bits = 0;
                object single = null;
                for (int i = 0; i < names.Length; i++)
                {
                    object value = null;
                    if (type.IsEnum)
                    {
                        value = Enum.Parse(type, names[i]);
                    }
                    else if (defOf != null)
                    {
                        FieldInfo f = AccessTools.Field(defOf, names[i]);
                        value = f != null ? f.GetValue(null) : null;
                    }
                    if (value == null)
                    {
                        continue;
                    }
                    if (single == null)
                    {
                        single = value;
                    }
                    bits |= Bits(value);
                }
                if (type.IsEnum)
                {
                    field.SetValue(layer, Enum.ToObject(type, bits));
                }
                else if (type == typeof(ulong))
                {
                    field.SetValue(layer, bits);
                }
                else if (type == typeof(long))
                {
                    field.SetValue(layer, (long)bits);
                }
                else if (single != null && type.IsInstanceOfType(single))
                {
                    field.SetValue(layer, single);
                }
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Could not tell the game when to redraw a layer: " + e.Message, 93611103);
            }
        }

        // The bit mask behind one change kind: an enum value or number as it is, or a def through
        // its conversion to a number (or its first whole-number field).
        private static ulong Bits(object value)
        {
            Type t = value.GetType();
            if (t.IsEnum || value is IConvertible)
            {
                return Convert.ToUInt64(value);
            }
            foreach (MethodInfo m in t.GetMethods(BindingFlags.Public | BindingFlags.Static))
            {
                if (m.Name == "op_Implicit" && (m.ReturnType == typeof(ulong) || m.ReturnType == typeof(long)))
                {
                    return Convert.ToUInt64(m.Invoke(null, new[] { value }));
                }
            }
            foreach (FieldInfo f in t.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
            {
                if (f.FieldType == typeof(ulong) || f.FieldType == typeof(long))
                {
                    return Convert.ToUInt64(f.GetValue(value));
                }
            }
            return 0;
        }

        public static void Clear()
        {
            queue.Clear();
            head = 0;
        }

        // Queues one layer of every block of a map. With onScreenFirst the blocks in view go first.
        public static void QueueAll(Map map, Type layer, bool onScreenFirst)
        {
            if (map == null || map.mapDrawer == null || layer == null)
            {
                return;
            }
            Look();
            Array sections = sectionsField != null ? sectionsField.GetValue(map.mapDrawer) as Array : null;
            if (sections == null || getLayer == null || sections.Rank != 2)
            {
                try
                {
                    MethodInfo all = AccessTools.Method(typeof(MapDrawer), "RegenerateEverythingNow");
                    if (all != null)
                    {
                        all.Invoke(map.mapDrawer, null);
                    }
                }
                catch (Exception e)
                {
                    Log.ErrorOnce("[IsoRim] Redrawing the map failed: " + e, 93611101);
                }
                return;
            }

            CellRect view = onScreenFirst && Find.CameraDriver != null ? Find.CameraDriver.CurrentViewRect : CellRect.Empty;
            int nx = sections.GetLength(0);
            int nz = sections.GetLength(1);
            List<Job> later = new List<Job>();
            for (int x = 0; x < nx; x++)
            {
                for (int z = 0; z < nz; z++)
                {
                    object s = sections.GetValue(x, z);
                    if (s == null)
                    {
                        continue;
                    }
                    Job job = new Job { map = map, section = s, layer = layer };
                    bool seen = onScreenFirst
                        && x * SectionSize <= view.maxX && (x + 1) * SectionSize > view.minX
                        && z * SectionSize <= view.maxZ && (z + 1) * SectionSize > view.minZ;
                    if (seen)
                    {
                        queue.Add(job);
                    }
                    else
                    {
                        later.Add(job);
                    }
                }
            }
            queue.AddRange(later);
        }

        // Queues one layer of the blocks within reach cells of c, other than c's own block (which
        // the game redraws itself), unless they are already waiting.
        public static void QueueAround(Map map, IntVec3 c, int reach, Type layer, bool includeOwn = false)
        {
            if (map == null || map.mapDrawer == null || layer == null)
            {
                return;
            }
            Look();
            Array sections = sectionsField != null ? sectionsField.GetValue(map.mapDrawer) as Array : null;
            if (sections == null || sections.Rank != 2 || getLayer == null)
            {
                return;
            }
            int own = c.x / SectionSize;
            int ownZ = c.z / SectionSize;
            int x0 = Math.Max(0, (c.x - reach) / SectionSize);
            int x1 = Math.Min(sections.GetLength(0) - 1, (c.x + reach) / SectionSize);
            int z0 = Math.Max(0, (c.z - reach) / SectionSize);
            int z1 = Math.Min(sections.GetLength(1) - 1, (c.z + reach) / SectionSize);
            for (int x = x0; x <= x1; x++)
            {
                for (int z = z0; z <= z1; z++)
                {
                    if (x == own && z == ownZ && !includeOwn)
                    {
                        continue;
                    }
                    object s = sections.GetValue(x, z);
                    if (s == null)
                    {
                        continue;
                    }
                    bool waiting = false;
                    for (int i = head; i < queue.Count; i++)
                    {
                        if (queue[i].section == s && queue[i].layer == layer)
                        {
                            waiting = true;
                            break;
                        }
                    }
                    if (!waiting)
                    {
                        queue.Add(new Job { map = map, section = s, layer = layer });
                    }
                }
            }
        }

        private static readonly System.Diagnostics.Stopwatch clock = new System.Diagnostics.Stopwatch();

        // Called every frame: redraws queued blocks until about four milliseconds have gone (at
        // least one, at most budget), so a big base is relit over a few frames without a hitch.
        public static void Process(int budget)
        {
            clock.Reset();
            clock.Start();
            if (head >= queue.Count)
            {
                if (queue.Count > 0)
                {
                    Clear();
                }
                return;
            }
            for (int done = 0; done < budget && head < queue.Count && (done == 0 || clock.ElapsedMilliseconds < 4); done++)
            {
                Job job = queue[head++];
                if (job.map == null || job.map.mapDrawer == null || !Find.Maps.Contains(job.map))
                {
                    continue;
                }
                try
                {
                    SectionLayer layer = getLayer.Invoke(job.section, new object[] { job.layer }) as SectionLayer;
                    if (layer != null)
                    {
                        layer.Regenerate();
                    }
                }
                catch (Exception e)
                {
                    Log.ErrorOnce("[IsoRim] Redrawing a block of the map failed: " + e, 93611102);
                }
            }
        }
    }
}
