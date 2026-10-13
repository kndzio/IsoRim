using System;
using System.Reflection;
using HarmonyLib;
using RimWorld;
using UnityEngine;
using Verse;

namespace IsoRim
{
    // Camera state and the maths shared by every other part of the mod.
    //
    // The game draws everything as flat quads on the ground and uses height (Y) only to decide
    // what is drawn on top of what. Seen from a tilted camera those layers would drift apart, so
    // the camera's view matrix multiplies Y by Squash. Anything that should really stand up has
    // its height divided by Squash to cancel that out. "Apparent space" below means the world
    // after squashing, which is what ends up on screen.
    public static class View3D
    {
        public const float MinPitch = 30f;
        public const float MaxPitch = 85f;
        public const float IsoYaw = 45f;   // how far the isometric camera is turned from north, clockwise seen from above

        // How far the lighting overlay is pulled toward the camera, and how much depth is kept
        // free either side of the visible ground.
        private const float OverlayPull = 30f;
        private const float DepthPad = 45f;

        public static bool Active;

        // Changes whenever a setting that affects the shape of things changes.
        public static int Stamp;

        public static Matrix4x4 LightingMatrix = Matrix4x4.identity;
        public static Matrix4x4 FogMatrix = Matrix4x4.identity;

        private static bool haveFrame;
        private static Vector3 eye;
        private static Vector3 fwd = Vector3.down;
        private static Vector3 up = Vector3.forward;
        private static Vector3 right = Vector3.right;
        private static float orthoSize = 20f;
        private static float aspect = 1.6f;

        private static Camera[] cams;
        private static bool camerasOverridden;

        private static bool lastActive;
        private static int appliedSig;
        private static int pendingSig;
        private static float pendingSince;

        private static readonly MethodInfo regenMethod = AccessTools.Method(typeof(MapDrawer), "RegenerateEverythingNow");

        public static bool Ready
        {
            get { return Active && haveFrame; }
        }

        // How steeply the camera looks down, in degrees: 90 is straight down.
        public static float Pitch
        {
            get
            {
                IsoRimSettings st = IsoRimMod.Settings;
                return Mathf.Clamp(st.isometric ? st.isoPitch : st.pitch, MinPitch, MaxPitch);
            }
        }

        // Which way the camera faces right now, in degrees clockwise from north seen from above.
        // 0 is the game's usual "north is up"; the isometric view starts out looking north-east.
        // It glides to YawTarget when the view is turned.
        public static float Yaw
        {
            get { return yawNow; }
        }

        // Where the camera is turning to: the base direction plus the eighth turns asked for.
        public static float YawTarget
        {
            get { return Mathf.Repeat((IsoRimMod.Settings.isometric ? IsoYaw : 0f) + 45f * Step, 360f); }
        }

        // How many eighth turns clockwise the view has been turned from its starting direction (0 to 7).
        // With 90 degree snaps this only ever takes even values.
        public static int Step
        {
            get { return ((IsoRimMod.Settings.turn % 8) + 8) % 8; }
        }

        // True while the camera is still swinging toward YawTarget.
        public static bool Turning
        {
            get { return yawSet && Mathf.Abs(Mathf.DeltaAngle(yawNow, YawTarget)) > 0.05f; }
        }

        private static float yawNow;
        private static bool yawSet;
        private const float TurnSpeed = 300f;   // degrees a second: an eighth turn takes about a sixth of a second

        private static void TurnCamera()
        {
            float target = YawTarget;
            if (!yawSet || !Active)
            {
                yawNow = target;
                yawSet = true;
            }
            else
            {
                // Eased: fast in the middle of the swing, gentle at the end, so a turn reads as smooth.
                float left = Mathf.Abs(Mathf.DeltaAngle(yawNow, target));
                float speed = TurnSpeed * Mathf.Clamp(left / 30f, 0.25f, 1.6f);
                yawNow = Mathf.Repeat(Mathf.MoveTowardsAngle(yawNow, target, speed * Time.unscaledDeltaTime), 360f);
            }
            // The light no longer follows the camera: the sun stays put in the world while the
            // camera turns round it (see SunStep), so turning never redraws anything.
        }

        // The direction along the ground that runs up the screen, away from the camera.
        public static Vector3 GroundForward
        {
            get
            {
                float y = Yaw * Mathf.Deg2Rad;
                return new Vector3(Mathf.Sin(y), 0f, Mathf.Cos(y));
            }
        }

        public static float Squash
        {
            // Kept very small: the game spaces its flat drawing layers far apart in height, and
            // whatever height is left after squashing shows as overlays (zone and drag
            // previews, field edges) floating off the ground.
            get { return Mathf.Clamp(IsoRimMod.Settings.squash, 0.002f, 0.004f); }
        }

        // The direction "up the sprite" points for anything stood up to face the camera.
        public static Vector3 CardUp
        {
            get
            {
                float p = Pitch * Mathf.Deg2Rad;
                float y = Yaw * Mathf.Deg2Rad;
                return new Vector3(Mathf.Sin(p) * Mathf.Sin(y), Mathf.Cos(p), Mathf.Sin(p) * Mathf.Cos(y));
            }
        }

        public static float WallHeight
        {
            get { return Mathf.Clamp(IsoRimMod.Settings.wallHeight, 0.5f, 4f); }
        }

        // Called once per frame from the map camera's update.
        public static void Tick()
        {
            if (Current.ProgramState != ProgramState.Playing || Current.Game == null)
            {
                return;
            }

            HandleKeys();
            TurnCamera();

            Camera main = Find.Camera;
            if (main == null)
            {
                return;
            }

            if (Active)
            {
                ApplyCamera(main);
                Looks.Draw(main);
            }
            else if (camerasOverridden)
            {
                ResetCamera();
            }

            RegenerateIfStateChanged();
            MapSections.Process(8);
            Ground.Sync();
            Cutaway.Process();
            if (Ready)
            {
                Cutaway.TrackPointer();
                Effects.DrawAll();
                try
                {
                    Interaction.DrawDragBox();
                    Interaction.DrawDesignationDrag();
                    Interaction.DrawDragGhosts();
                }
                catch (Exception e)
                {
                    Log.ErrorOnce("[IsoRim] Drawing the drag box or ghosts failed: " + e, 93611163);
                }
            }
        }

        private static void HandleKeys()
        {
            // Keys are ignored while a text box has focus, so typing a 0 does not flip the view.
            bool typing = GUIUtility.keyboardControl != 0;

            if (!typing && R3DKeyDefOf.R3D_ToggleView != null && R3DKeyDefOf.R3D_ToggleView.JustPressed)
            {
                Active = !Active;
                Messages.Message(Active ? "IsoRim: 3D view on" : "IsoRim: 3D view off", MessageTypeDefOf.SilentInput, false);
            }

            if (!typing && R3DKeyDefOf.R3D_Isometric != null && R3DKeyDefOf.R3D_Isometric.JustPressed)
            {
                // From the flat game this goes straight to isometric; after that it swaps
                // between isometric and the straight-on 3D view.
                IsoRimSettings st = IsoRimMod.Settings;
                st.isometric = !Active || !st.isometric;
                Active = true;
                Messages.Message(st.isometric ? "IsoRim: isometric view" : "IsoRim: straight-on view", MessageTypeDefOf.SilentInput, false);
            }

            if (!Active || typing)
            {
                return;
            }

            // Q and E turn the view an eighth or a quarter turn (see the options). The game uses the
            // same keys to turn a building that is being placed, so they are left alone while
            // something is selected to build.
            if (Find.DesignatorManager == null || Find.DesignatorManager.SelectedDesignator == null)
            {
                IsoRimSettings turnSettings = IsoRimMod.Settings;
                if (R3DKeyDefOf.R3D_TurnLeft != null && R3DKeyDefOf.R3D_TurnLeft.JustPressed)
                {
                    turnSettings.turn = TurnBy(turnSettings.turn, -1, turnSettings.snap45);
                }
                if (R3DKeyDefOf.R3D_TurnRight != null && R3DKeyDefOf.R3D_TurnRight.JustPressed)
                {
                    turnSettings.turn = TurnBy(turnSettings.turn, 1, turnSettings.snap45);
                }
            }
            if (R3DKeyDefOf.R3D_ToggleRoofs != null && R3DKeyDefOf.R3D_ToggleRoofs.JustPressed)
            {
                Roofs.Toggle();
            }

            float dir = 0f;
            if (R3DKeyDefOf.R3D_TiltUp != null && R3DKeyDefOf.R3D_TiltUp.IsDown)
            {
                dir += 1f;
            }
            if (R3DKeyDefOf.R3D_TiltDown != null && R3DKeyDefOf.R3D_TiltDown.IsDown)
            {
                dir -= 1f;
            }
            if (dir != 0f)
            {
                IsoRimSettings s = IsoRimMod.Settings;
                float change = dir * 40f * Time.unscaledDeltaTime;
                if (s.isometric)
                {
                    s.isoPitch = Mathf.Clamp(s.isoPitch + change, MinPitch, MaxPitch);
                }
                else
                {
                    s.pitch = Mathf.Clamp(s.pitch + change, MinPitch, MaxPitch);
                }
            }
        }

        // One step left (-1) or right (+1) from an eighth-turn count. With quarter snaps an odd
        // count (left over from the eighth snaps) lands on the nearest quarter in that direction.
        public static int TurnBy(int turn, int dir, bool eighths)
        {
            turn = ((turn % 8) + 8) % 8;
            if (eighths)
            {
                return (turn + dir + 8) % 8;
            }
            if (dir > 0)
            {
                return ((turn / 2) + 1) * 2 % 8;
            }
            return (turn % 2 == 1 ? turn - 1 : turn - 2 + 8) % 8;
        }

        private static void ApplyCamera(Camera main)
        {
            if (cams == null || cams.Length == 0 || cams[0] == null)
            {
                // The main camera plus the helper cameras the game hangs under it (water depth etc.),
                // which have to look from the same place or their effects stop lining up.
                cams = main.GetComponentsInChildren<Camera>(true);
            }

            float pitchDeg = Pitch;
            float p = pitchDeg * Mathf.Deg2Rad;
            float s = Squash;

            orthoSize = main.orthographicSize;
            aspect = main.aspect;

            // The game keeps the camera directly above the point at the centre of the screen.
            // The transform is left alone so everything that reads it keeps working.
            Vector3 tp = main.transform.position;
            Vector3 focus = new Vector3(tp.x, 0f, tp.z);

            Quaternion look = Quaternion.Euler(pitchDeg, Yaw, 0f);
            fwd = look * Vector3.forward;
            up = look * Vector3.up;
            right = look * Vector3.right;

            float half = orthoSize / Mathf.Tan(p) + DepthPad;
            eye = focus - fwd * (half + 5f);
            float far = 2f * half + 10f;

            Matrix4x4 view = Matrix4x4.Scale(new Vector3(1f, 1f, -1f))
                * Matrix4x4.TRS(eye, look, Vector3.one).inverse;
            Matrix4x4 worldToCamera = view * Matrix4x4.Scale(new Vector3(1f, s, 1f));

            for (int i = 0; i < cams.Length; i++)
            {
                Camera c = cams[i];
                if (c == null)
                {
                    continue;
                }
                float size = c.orthographicSize;
                float asp = c.aspect;
                Matrix4x4 proj = Matrix4x4.Ortho(-size * asp, size * asp, -size, size, 0.5f, far);
                c.worldToCameraMatrix = worldToCamera;
                c.projectionMatrix = proj;
                c.cullingMatrix = proj * worldToCamera;
            }
            camerasOverridden = true;
            haveFrame = true;

            // Moving something straight toward an orthographic camera does not move it on screen,
            // it only puts it in front. That is how the lighting overlay gets to darken upright things.
            LightingMatrix = Matrix4x4.Translate(new Vector3(-fwd.x * OverlayPull, -fwd.y * OverlayPull / s, -fwd.z * OverlayPull));
            FogMatrix = Matrix4x4.Translate(new Vector3(0f, WallHeight / s, 0f));
        }

        private static void ResetCamera()
        {
            if (cams != null)
            {
                for (int i = 0; i < cams.Length; i++)
                {
                    Camera c = cams[i];
                    if (c == null)
                    {
                        continue;
                    }
                    c.ResetWorldToCameraMatrix();
                    c.ResetProjectionMatrix();
                    c.ResetCullingMatrix();
                }
            }
            cams = null;
            camerasOverridden = false;
            haveFrame = false;
        }

        // Baked map geometry (walls, models, plants) depends on these values, so the map is
        // rebuilt when they change. Angle changes wait until the key is released.
        private static int StateSignature()
        {
            if (!Active)
            {
                return 0;
            }
            IsoRimSettings st = IsoRimMod.Settings;
            unchecked
            {
                int h = 17;
                h = h * 31 + Mathf.RoundToInt(Pitch * 2f);
                // The camera's turn is not part of this: it only changes the baked shading, which
                // is relit separately once the camera comes to rest (see Relight).
                h = h * 31 + Mathf.RoundToInt(Squash * 10000f);
                h = h * 31 + Mathf.RoundToInt(WallHeight * 100f);
                h = h * 31 + (st.uprightPlants ? 1 : 0);
                h = h * 31 + (st.walls3D ? 1 : 0);
                h = h * 31 + (st.texturedWalls ? 1 : 0);
                h = h * 31 + (st.autoExtrude ? 1 : 0);
                h = h * 31 + (st.thickItems ? 1 : 0);
                h = h * 31 + (st.itemsFromArt ? 1 : 0);
                h = h * 31 + Mathf.RoundToInt(st.itemThickness * 20f);
                h = h * 31 + (st.ghosts3D ? 1 : 0);
                h = h * 31 + (st.cutRock ? 1 : 0);
                h = h * 31 + (st.mapEdge3D ? 1 : 0);
                h = h * 31 + (st.damage3D ? 1 : 0);
                h = h * 31 + (st.outlines ? 1 : 0);
                h = h * 31 + (st.texturedModels ? 1 : 0);
                h = h * 31 + (st.ruggedRock ? 1 : 0);
                h = h * 31 + (st.trees3D ? 1 : 0);
                h = h * 31 + (st.smallPlants3D ? 1 : 0);
                h = h * 31 + (st.models3D ? 1 : 0);
                h = h * 31 + (st.groundShadows ? 1 : 0);
                h = h * 31 + (st.waterStyle ? 1 : 0);
                h = h * 31 + (st.cutRooms ? 1 : 0);
                h = h * 31 + Mathf.RoundToInt(st.cutHeight * 100f);
                h = h * 31 + (st.treeShadows ? 1 : 0);
                h = h * 31 + Mathf.RoundToInt(st.treeShadowLength * 100f);
                return h == 0 ? 1 : h;
            }
        }

        private static void RegenerateIfStateChanged()
        {
            int sig = StateSignature();
            Stamp = sig;
            bool toggled = Active != lastActive;
            lastActive = Active;

            if (sig == appliedSig)
            {
                pendingSig = sig;
                Relight();
                return;
            }

            if (!toggled)
            {
                if (sig != pendingSig)
                {
                    pendingSig = sig;
                    pendingSince = Time.realtimeSinceStartup;
                    return;
                }
                if (Time.realtimeSinceStartup - pendingSince < 0.35f)
                {
                    return;
                }
            }

            appliedSig = sig;
            pendingSig = sig;
            R3DMaterials.SetSunHour(SunHour());
            MapSections.Clear();
            RegenerateAllMaps();
        }

        // The sun moves smoothly with the time of day. Everything that stays put is lit through
        // materials whose colour follows it (see R3DMaterials.Lit), so nothing is redrawn as it
        // moves; moving things remake their meshes once per game hour.
        private static void Relight()
        {
            if (!Active)
            {
                return;
            }
            R3DMaterials.SetSunHour(SunHour());

            // Which walls are cut down to show the rooms behind them depends on which way the
            // camera looks, so once it comes to rest facing a new way those are redrawn.
            int step = Step;
            if (litFacing < 0)
            {
                litFacing = step;
            }
            else if (step != litFacing && !Turning)
            {
                litFacing = step;
                foreach (Map map in Find.Maps)
                {
                    bool here = map == Find.CurrentMap;
                    MapSections.QueueAll(map, typeof(SectionLayer_IsoRimWalls), here);
                    MapSections.QueueAll(map, typeof(SectionLayer_IsoRimDamage), here);
                    MapSections.QueueAll(map, typeof(SectionLayer_IsoRimEdge), here);
                    if (IsoRimMod.Settings.showRoofs)
                    {
                        MapSections.QueueAll(map, typeof(SectionLayer_IsoRimRoofs), here);
                    }
                    if (!IsoRimMod.Settings.texturedWalls)
                    {
                        MapSections.QueueAll(map, MapSections.ThingsLayer, here);
                    }
                }
            }
        }

        private static int litFacing = -1;

        // The hour the sun is at: the current map's time of day, or mid-morning with
        // "Sun moves through the day" off.
        public static float SunHour()
        {
            IsoRimSettings st = IsoRimMod.Settings;
            Map map = Find.CurrentMap;
            if (!st.sunMoves || map == null)
            {
                return 9.5f;
            }
            return GenLocalDate.HourFloat(map);
        }

        private static void RegenerateAllMaps()
        {
            if (regenMethod == null)
            {
                Log.ErrorOnce("[IsoRim] MapDrawer.RegenerateEverythingNow was not found, so walls and models will not refresh.", 93611001);
                return;
            }
            foreach (Map map in Find.Maps)
            {
                try
                {
                    regenMethod.Invoke(map.mapDrawer, null);
                }
                catch (Exception e)
                {
                    Log.ErrorOnce("[IsoRim] Rebuilding the map drawing failed: " + e, 93611002);
                }
            }
        }

        // Screen pixel (origin bottom left) to the point on the ground under it.
        public static Vector3 ScreenToGround(Vector2 px)
        {
            float nx = px.x / Screen.width * 2f - 1f;
            float ny = px.y / Screen.height * 2f - 1f;
            Vector3 origin = eye + right * (nx * orthoSize * aspect) + up * (ny * orthoSize);
            float t = -origin.y / fwd.y;
            Vector3 hit = origin + fwd * t;
            return new Vector3(hit.x, 0f, hit.z);
        }

        // Where the line of sight through a screen point (pixels, from the bottom left) is at a
        // given height above the ground, in cells.
        public static Vector3 ScreenToHeight(Vector2 px, float height)
        {
            float nx = px.x / Screen.width * 2f - 1f;
            float ny = px.y / Screen.height * 2f - 1f;
            Vector3 origin = eye + right * (nx * orthoSize * aspect) + up * (ny * orthoSize);
            float t = (height - origin.y) / fwd.y;
            Vector3 hit = origin + fwd * t;
            return new Vector3(hit.x, height, hit.z);
        }

        // The corners of a sheet that covers the screen, a given distance in front of the camera:
        // bottom left, top left, top right, bottom right. margin 1 fits the screen exactly.
        public static void ScreenCorners(float distance, float margin, Vector3[] into)
        {
            Vector3 centre = eye + fwd * distance;
            Vector3 across = right * (orthoSize * aspect * margin);
            Vector3 upward = up * (orthoSize * margin);
            into[0] = Unsquashed(centre - across - upward);
            into[1] = Unsquashed(centre - across + upward);
            into[2] = Unsquashed(centre + across + upward);
            into[3] = Unsquashed(centre + across - upward);
        }

        // From a point as it appears on screen back to where it has to be put in the game's
        // world, whose heights the camera multiplies by Squash.
        private static Vector3 Unsquashed(Vector3 apparent)
        {
            return new Vector3(apparent.x, apparent.y / Squash, apparent.z);
        }

        // The block of map cells that can be seen, used by the game to decide what to draw.
        public static CellRect GroundRect()
        {
            // With the camera turned, the screen is a slanted rectangle on the ground, so all
            // four corners count.
            Vector3 a = ScreenToGround(new Vector2(0f, 0f));
            Vector3 b = ScreenToGround(new Vector2(Screen.width, Screen.height));
            Vector3 c = ScreenToGround(new Vector2(0f, Screen.height));
            Vector3 d = ScreenToGround(new Vector2(Screen.width, 0f));
            CellRect r = new CellRect();
            r.minX = Mathf.FloorToInt(Mathf.Min(Mathf.Min(a.x, b.x), Mathf.Min(c.x, d.x))) - 2;
            r.maxX = Mathf.CeilToInt(Mathf.Max(Mathf.Max(a.x, b.x), Mathf.Max(c.x, d.x))) + 2;
            r.minZ = Mathf.FloorToInt(Mathf.Min(Mathf.Min(a.z, b.z), Mathf.Min(c.z, d.z))) - 2;
            r.maxZ = Mathf.CeilToInt(Mathf.Max(Mathf.Max(a.z, b.z), Mathf.Max(c.z, d.z))) + 2;

            // Extra room on the sides nearest the camera: tall things just off those screen
            // edges still poke into view.
            Vector3 f = GroundForward;
            if (f.z > 0.3f)
            {
                r.minZ -= 6;
            }
            else if (f.z < -0.3f)
            {
                r.maxZ += 6;
            }
            if (f.x > 0.3f)
            {
                r.minX -= 6;
            }
            else if (f.x < -0.3f)
            {
                r.maxX += 6;
            }
            return r;
        }

        // Stands a flat sprite up so that it faces the camera, hinged at pivot.
        public static Matrix4x4 UprightMatrix(Vector3 pivot)
        {
            return Matrix4x4.Translate(pivot)
                * Matrix4x4.Scale(new Vector3(1f, 1f / Squash, 1f))
                * Matrix4x4.Rotate(Quaternion.Euler(Pitch - 90f, Yaw, 0f))
                * Matrix4x4.Translate(-pivot);
        }

        // Same as UprightMatrix, for a single point.
        public static Vector3 UprightPoint(Vector3 v, Vector3 pivot)
        {
            float a = (Pitch - 90f) * Mathf.Deg2Rad;
            float cos = Mathf.Cos(a);
            float sin = Mathf.Sin(a);
            float dx = v.x - pivot.x;
            float dy = v.y - pivot.y;
            float dz = v.z - pivot.z;
            float y2 = dy * cos - dz * sin;
            float z2 = dy * sin + dz * cos;

            // Tilted up, then turned about the vertical to face the camera.
            float yaw = Yaw * Mathf.Deg2Rad;
            float cy = Mathf.Cos(yaw);
            float sy = Mathf.Sin(yaw);
            return new Vector3(pivot.x + dx * cy + z2 * sy, pivot.y + y2 / Squash, pivot.z - dx * sy + z2 * cy);
        }

        // Turns a movement given in screen terms (x to the right, y up the screen) into one along
        // the ground. With exact set, a movement up the screen is also stretched to make up for
        // the ground being seen at a slant, so that a dragged map stays under the pointer.
        public static Vector2 ScreenMoveToGround(Vector2 move, bool exact)
        {
            float y = move.y;
            if (exact)
            {
                y /= Mathf.Max(0.2f, Mathf.Sin(Pitch * Mathf.Deg2Rad));
            }
            float yaw = Yaw * Mathf.Deg2Rad;
            float cy = Mathf.Cos(yaw);
            float sy = Mathf.Sin(yaw);
            return new Vector2(move.x * cy + y * sy, -move.x * sy + y * cy);
        }

        // Raises something by a real height, in cells, without tilting it.
        public static Matrix4x4 LiftMatrix(float height)
        {
            return Matrix4x4.Translate(new Vector3(0f, height / Squash, 0f));
        }
    }
}
