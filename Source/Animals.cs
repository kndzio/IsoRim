using System;
using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;

namespace IsoRim
{
    // Animals drawn as 3D models in place of their sprites.
    //
    // An animal is a body model and one leg model drawn once at each hip (see the animal
    // entries in Defs/Models.xml). Unlike a sprite, which only has four facings, the model
    // turns to face the way the animal is actually walking, and its legs swing in step with
    // the ground it covers. Asleep it settles onto its belly with its legs folded away; downed
    // or dead it lies on its side.
    public static class Animals
    {
        // What has to be remembered about one animal from frame to frame.
        private class State
        {
            public float yaw;       // the way it is drawn facing, degrees clockwise from north
            public float heading;   // the way it is turning toward
            public float phase;     // where the legs are in their swing, radians
            public float gait;      // 0 standing still, 1 in full stride
            public Vector3 last;    // where it was drawn last
            public int frame;       // and when
        }

        private static readonly Dictionary<int, State> states = new Dictionary<int, State>();
        private static readonly List<int> stale = new List<int>();

        // Draws the animal at drawLoc. Returns false if it has no model, in which case the
        // game's sprite must be drawn as usual.
        public static bool Draw(Pawn pawn, Vector3 drawLoc)
        {
            ModelEntry entry;
            if (pawn.def == null || !ModelLibrary.TryGet(pawn.def, out entry) || !entry.def.animal || !entry.HasModel)
            {
                return false;
            }
            ModelDef def = entry.def;
            Model body = entry.Pick(pawn);
            if (body == null)
            {
                return false;
            }

            float size = def.scale * SizeOf(pawn);
            bool dead = pawn.Dead;
            bool lying = dead || pawn.GetPosture() != PawnPosture.Standing;
            bool onSide = dead || pawn.Downed;

            float yaw;
            float phase = 0f;
            float gait = 0f;
            if (dead)
            {
                // Each carcass lies at its own slight angle.
                yaw = pawn.Rotation.AsAngle + (Hashing.Unit(pawn.thingIDNumber, 3, 9) - 0.5f) * 50f;
            }
            else
            {
                State st = Advance(pawn, drawLoc, lying, def.stride * size);
                yaw = st.yaw;
                phase = st.phase;
                gait = st.gait;
            }

            float ground = 0f;
            if (lying && !dead)
            {
                Building_Bed bed = pawn.CurrentBed();
                if (bed != null)
                {
                    ground = Forms.HeightOf(bed);
                }
            }
            Vector3 position = new Vector3(drawLoc.x, ground, drawLoc.z);
            Matrix4x4 sized = Matrix4x4.Scale(new Vector3(size, size, size));

            // How the whole animal is posed, before it is turned to face its heading.
            Matrix4x4 bodyPose;
            Matrix4x4 legPose = Matrix4x4.identity;
            bool drawLegs = true;
            if (onSide)
            {
                // Rolled over about the middle of its trunk, which then rests on the ground.
                bodyPose = Matrix4x4.Translate(new Vector3(0f, def.bodyHalfWidth * size, 0f))
                    * Matrix4x4.Rotate(Quaternion.AngleAxis(90f, Vector3.forward))
                    * Matrix4x4.Translate(new Vector3(0f, -def.bodyCentre * size, 0f));
                legPose = bodyPose;
                gait = 0f;
            }
            else if (lying)
            {
                bodyPose = Matrix4x4.Translate(new Vector3(0f, -def.legLength * size * 0.78f, 0f));
                drawLegs = false;
            }
            else
            {
                // A slight rise and fall with each step.
                float bob = Mathf.Abs(Mathf.Sin(phase)) * 0.05f * def.legLength * size * gait;
                bodyPose = Matrix4x4.Translate(new Vector3(0f, bob, 0f));
            }

            DynamicModels.DrawLocal(body, position, yaw, bodyPose * sized, Color.white, null);
            if (ground <= 0f)
            {
                GroundShadows.Blob(position, yaw, def.bodyHalfWidth * size * 1.5f, def.bodyHalfLength * size * 1.25f);
            }

            if (drawLegs && entry.leg != null && def.legs != null)
            {
                Matrix4x4 drop = Matrix4x4.Translate(new Vector3(0f, -def.legLength, 0f));
                for (int i = 0; i < def.legs.Count; i++)
                {
                    Vector3 hip = def.legs[i];

                    // Legs at opposite corners move together, as in a trot.
                    float beat = ((i + i / 2) % 2) * Mathf.PI;
                    float swing = gait > 0.01f ? Mathf.Sin(phase + beat) * Mathf.Min(def.legSwing, 40f) * Mathf.Clamp01(gait) : 0f;
                    float splay = hip.x >= 0f ? def.legSplay : -def.legSplay;
                    Quaternion turn = Quaternion.AngleAxis(splay, Vector3.forward) * Quaternion.AngleAxis(swing, Vector3.right);

                    Matrix4x4 local = legPose * sized * Matrix4x4.Translate(hip) * Matrix4x4.Rotate(turn) * drop;
                    DynamicModels.DrawLocal(entry.leg, position, yaw, local, Color.white, null);
                }
            }
            return true;
        }

        // The same turning and stepping for anything else that walks (people). Gives back the
        // way it should face, where it is in its stride and how much of a stride it is in.
        public static void Track(Pawn pawn, Vector3 drawLoc, bool lying, float stride, out float yaw, out float phase, out float gait)
        {
            State st = Advance(pawn, drawLoc, lying, stride);
            yaw = st.yaw;
            phase = st.phase;
            gait = st.gait;
        }

        // Young animals are smaller. The game's own measure of body size shrinks much faster
        // than the animal looks, so it is eased.
        private static float SizeOf(Pawn pawn)
        {
            float factor = 1f;
            if (pawn.ageTracker != null && pawn.ageTracker.CurLifeStage != null)
            {
                factor = pawn.ageTracker.CurLifeStage.bodySizeFactor;
            }
            return Mathf.Lerp(0.5f, 1f, Mathf.Clamp01(factor));
        }

        // Moves one animal's facing and leg swing on by a frame.
        private static State Advance(Pawn pawn, Vector3 drawLoc, bool lying, float stride)
        {
            int id = pawn.thingIDNumber;
            int frame = Time.frameCount;
            float facing = pawn.Rotation.AsAngle;

            State st;
            if (!states.TryGetValue(id, out st))
            {
                st = new State();
                st.yaw = facing;
                st.heading = facing;
                st.last = drawLoc;
                st.frame = frame;
                states[id] = st;
                Prune(frame);
                return st;
            }
            if (st.frame == frame)
            {
                return st;   // drawn twice in one frame
            }

            bool fresh = frame - st.frame <= 2;   // it was on screen a moment ago
            Vector3 move = drawLoc - st.last;
            move.y = 0f;
            float dist = move.magnitude;
            float dt = Time.deltaTime;

            if (!lying && fresh && dist > 0.0004f && dist < 1.5f)
            {
                // Walking: face the way it is going, and swing the legs by the ground covered.
                st.heading = Mathf.Atan2(move.x, move.z) * Mathf.Rad2Deg;
                // Capped per frame: at high game speed a fast animal covers several strides
                // between frames, and stepping the swing by all of that would make the legs
                // jump to random angles (a blur of spikes) instead of running.
                st.phase += Mathf.Min(dist / Mathf.Max(0.2f, stride) * 2f * Mathf.PI, 0.55f);
                if (st.phase > 6283f)
                {
                    st.phase -= 6283.1853f;   // a thousand whole swings
                }
                st.gait = Mathf.MoveTowards(st.gait, 1f, dt * 8f);
            }
            else if (lying || pawn.pather == null || !pawn.pather.Moving)
            {
                // Standing still: turn to the facing the game gives it and bring the legs together.
                st.heading = facing;
                st.gait = Mathf.MoveTowards(st.gait, 0f, dt * 5f);
            }
            // Otherwise it is in mid-walk but did not move this frame (the game is paused): hold the pose.

            st.yaw = fresh ? Mathf.MoveTowardsAngle(st.yaw, st.heading, 500f * dt) : st.heading;
            st.last = drawLoc;
            st.frame = frame;
            return st;
        }

        // Forgets animals that have not been drawn for a while (dead, gone, or left behind on another map).
        private static void Prune(int frame)
        {
            if (states.Count < 400)
            {
                return;
            }
            stale.Clear();
            foreach (KeyValuePair<int, State> pair in states)
            {
                if (frame - pair.Value.frame > 600)
                {
                    stale.Add(pair.Key);
                }
            }
            for (int i = 0; i < stale.Count; i++)
            {
                states.Remove(stale[i]);
            }
        }
    }
}
