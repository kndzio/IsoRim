using System;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI;

namespace IsoRim
{
    // Colonists at work: they turn to face what they are working on, lean into each stroke and
    // swing the right tool for the job. An axe for felling trees, a pickaxe at the rock face, a
    // scythe through crops, a hammer on anything being built, repaired or taken down, a hoe
    // for sowing, a broom for cleaning, a knife at the butcher's table, and a steady bob over
    // any other bench or desk. Everything is timed by game ticks, so it stops when paused and
    // speeds up with the game.
    public static class WorkAnimations
    {
        private enum Motion
        {
            Chop,    // overhead, down on the work
            Sweep,   // side to side, low
            Bob      // no tool: a gentle lean over the work
        }

        private class Kind
        {
            public string model;
            public Motion motion;
            public float period;     // ticks per stroke
            public float raised;     // tool angle at the top of the stroke, degrees forward from upright
            public float struck;     // at the bottom of the stroke
            public float lean;       // how far the body leans into the stroke, degrees
            public Vector3 hand;     // where the tool is held, in the figure's own space (cells)
            public Model loaded;
            public bool tried;
        }

        private static readonly Kind Axe = new Kind { model = "tool_axe", motion = Motion.Chop, period = 70f, raised = -40f, struck = 100f, lean = 8f, hand = new Vector3(0.10f, 0.50f, 0.14f) };
        private static readonly Kind Pickaxe = new Kind { model = "tool_pickaxe", motion = Motion.Chop, period = 80f, raised = -50f, struck = 105f, lean = 10f, hand = new Vector3(0.08f, 0.50f, 0.14f) };
        private static readonly Kind Hammer = new Kind { model = "tool_hammer", motion = Motion.Chop, period = 34f, raised = 5f, struck = 95f, lean = 5f, hand = new Vector3(0.16f, 0.46f, 0.16f) };
        private static readonly Kind Hoe = new Kind { model = "tool_hoe", motion = Motion.Chop, period = 78f, raised = 0f, struck = 115f, lean = 9f, hand = new Vector3(0.08f, 0.46f, 0.14f) };
        private static readonly Kind Knife = new Kind { model = "tool_knife", motion = Motion.Chop, period = 30f, raised = 40f, struck = 110f, lean = 6f, hand = new Vector3(0.16f, 0.44f, 0.18f) };
        private static readonly Kind Scythe = new Kind { model = "tool_scythe", motion = Motion.Sweep, period = 64f, raised = 112f, struck = 40f, lean = 7f, hand = new Vector3(0.10f, 0.40f, 0.10f) };
        private static readonly Kind Broom = new Kind { model = "tool_broom", motion = Motion.Sweep, period = 40f, raised = 122f, struck = 28f, lean = 6f, hand = new Vector3(0.08f, 0.52f, 0.10f) };
        private static readonly Kind Hands = new Kind { model = null, motion = Motion.Bob, period = 90f, lean = 5f };

        // True if the pawn is working at something with an animation. yaw is turned to face the
        // work; tool (if any) is drawn with toolLocal in the figure's own space; lean and dip
        // bend the whole figure into the stroke.
        public static bool Animate(Pawn pawn, Vector3 drawLoc, ref float yaw, out Model tool, out Matrix4x4 toolLocal, out float lean, out float dip)
        {
            tool = null;
            toolLocal = Matrix4x4.identity;
            lean = 0f;
            dip = 0f;
            try
            {
                IntVec3 target;
                Kind kind = KindFor(pawn, out target);
                if (kind == null)
                {
                    return false;
                }
                Vector3 to = target.ToVector3Shifted() - drawLoc;
                if (to.x * to.x + to.z * to.z > 0.04f)
                {
                    yaw = to.AngleFlat();
                }

                float ticks = Find.TickManager.TicksGame + (pawn.thingIDNumber % 97);
                float p = Mathf.Repeat(ticks / kind.period, 1f);
                float swing;      // the tool's angle for Chop, the side to side angle for Sweep
                float effort;     // 0 resting, 1 at the moment of the blow
                switch (kind.motion)
                {
                    case Motion.Chop:
                        if (p < 0.55f)
                        {
                            // Wind up: slow and smooth.
                            float k = Mathf.SmoothStep(0f, 1f, p / 0.55f);
                            swing = Mathf.Lerp(kind.struck, kind.raised, k);
                            effort = 0.2f * (1f - k);
                        }
                        else if (p < 0.70f)
                        {
                            // The blow: fast, speeding up.
                            float k = (p - 0.55f) / 0.15f;
                            k *= k;
                            swing = Mathf.Lerp(kind.raised, kind.struck, k);
                            effort = k;
                        }
                        else
                        {
                            // Follow-through: a small bounce off the work.
                            float k = (p - 0.70f) / 0.30f;
                            swing = kind.struck - 7f * Mathf.Sin(k * Mathf.PI);
                            effort = 1f - k;
                        }
                        break;
                    case Motion.Sweep:
                        swing = Mathf.Sin(p * Mathf.PI * 2f) * kind.struck;
                        effort = 0.5f + 0.5f * Mathf.Abs(Mathf.Sin(p * Mathf.PI * 2f));
                        break;
                    default:
                        swing = 0f;
                        effort = 0.5f + 0.5f * Mathf.Sin(p * Mathf.PI * 2f);
                        break;
                }

                lean = kind.lean * effort;
                dip = 0.02f * effort;
                if (kind.model == null)
                {
                    return true;
                }
                if (!kind.tried)
                {
                    kind.tried = true;
                    kind.loaded = People.Part(kind.model);
                }
                tool = kind.loaded;
                if (tool == null)
                {
                    return true;
                }
                if (kind.motion == Motion.Chop)
                {
                    // Turning about X tips the handle forward, bringing the head down in front.
                    toolLocal = Matrix4x4.Translate(kind.hand) * Matrix4x4.Rotate(Quaternion.AngleAxis(swing, Vector3.right));
                }
                else
                {
                    // Tipped well forward so the working end is down by the ground, then swung
                    // from side to side about the hands.
                    toolLocal = Matrix4x4.Translate(kind.hand)
                        * Matrix4x4.Rotate(Quaternion.AngleAxis(swing, Vector3.up))
                        * Matrix4x4.Rotate(Quaternion.AngleAxis(kind.raised, Vector3.right));
                }
                return true;
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Working out a work animation failed: " + e, 93611140);
                return false;
            }
        }

        private static Kind KindFor(Pawn pawn, out IntVec3 target)
        {
            target = IntVec3.Invalid;
            Job job = pawn.CurJob;
            if (job == null || job.def == null || pawn.Drafted || (pawn.pather != null && pawn.pather.Moving))
            {
                return null;
            }
            LocalTargetInfo a = job.targetA;
            if (!a.IsValid)
            {
                return null;
            }
            target = a.Cell;
            // Only once they have reached the work, not while fetching things for it.
            if (target.IsValid && pawn.Position.DistanceToSquared(target) > 8)
            {
                return null;
            }

            switch (job.def.defName)
            {
                case "CutPlant":
                case "CutPlantDesignated":
                case "Harvest":
                case "HarvestDesignated":
                {
                    Plant plant = a.Thing as Plant;
                    return plant != null && plant.def.plant != null && plant.def.plant.IsTree ? Axe : Scythe;
                }
                case "Mine":
                    return Pickaxe;
                case "FinishFrame":
                case "Repair":
                case "BuildRoof":
                case "RemoveRoof":
                case "Deconstruct":
                case "Uninstall":
                case "SmoothFloor":
                case "SmoothWall":
                case "RemoveFloor":
                case "FixBrokenDownBuilding":
                case "PlaceNoCostFrame":
                    return Hammer;
                case "Sow":
                    return Hoe;
                case "Clean":
                    return Broom;
                case "Research":
                    return Hands;
                case "DoBill":
                {
                    string bench = a.Thing != null && a.Thing.def != null ? (a.Thing.def.defName ?? "") : "";
                    if (bench.Contains("Butcher"))
                    {
                        return Knife;
                    }
                    if (bench.Contains("Smithy") || bench.Contains("Machining") || bench.Contains("Fabrication") || bench.Contains("Stonecutter")
                        || bench.Contains("Sculpt") || bench.Contains("Crafting") || bench.Contains("Smelter"))
                    {
                        return Hammer;
                    }
                    return Hands;
                }
            }
            return null;
        }
    }
}
