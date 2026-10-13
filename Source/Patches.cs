using System;
using System.Collections.Generic;
using System.Reflection;
using System.Reflection.Emit;
using HarmonyLib;
using RimWorld;
using UnityEngine;
using Verse;

namespace IsoRim
{
    // Every hook into the game lives here. Each one is applied on its own, so if a game update
    // renames something, that one feature logs a warning and switches itself off while the rest
    // keep working. With the 3D view off, every hook passes straight through to the original.
    public static class Patches
    {
        private static Harmony harmony;
        private static AccessTools.FieldRef<PawnRenderer, Pawn> pawnOfRenderer;
        private static readonly List<FieldInfo> dragFields = new List<FieldInfo>();   // the game's own camera movement, cleared while the mod drags
        private static bool dragging;
        private static Vector3 dragAnchor;     // the point on the ground that was under the pointer when the drag began
        private static Vector3 dragStartPos;   // where the camera was at the start of this frame

        // Set while a standing pawn is being drawn: where its feet are and how big it is
        // compared with a person.
        private static bool pawnUpright;
        private static bool pawnFigure;      // the pawn being drawn is a 3D figure
        private static float pawnFacing;     // which way it faces, degrees clockwise from north
        private static float pawnHandHeight; // how high it holds a weapon, in cells
        private static Vector3 pawnFeet;
        private static float pawnSize = 1f;
        private const float HandHeight = 0.55f;   // up the sprite from the feet, in cells
        private const float HandReach = 0.2f;     // how far in front of the pawn the weapon is held
        private static readonly Dictionary<Type, int> layerKinds = new Dictionary<Type, int>();

        public static void ApplyAll()
        {
            harmony = new Harmony("isorim.core");

            Patch("camera", AccessTools.Method(typeof(CameraDriver), "Update"),
                postfix: nameof(CameraUpdate_Postfix));

            // Moving the camera: the game moves it along the map's own axes, which only match
            // the screen while north is up.
            Patch("camera movement in the isometric view", AccessTools.Method(typeof(CameraDriver), "CalculateCurInputDollyVect"),
                postfix: nameof(DollyVect_Postfix));
            // Dragging the map with the middle mouse button: done by the mod while the 3D view is on,
            // so the ground stays under the pointer whichever way the camera is turned.
            foreach (string name in new[] { "desiredDollyRaw", "desiredDolly", "mouseDragVect" })
            {
                FieldInfo f = AccessTools.Field(typeof(CameraDriver), name);
                if (f != null && f.FieldType == typeof(Vector2))
                {
                    dragFields.Add(f);
                }
            }
            Patch("map dragging", AccessTools.Method(typeof(CameraDriver), "Update"), prefix: nameof(CameraUpdate_Prefix));

            // Dragging a selection box, and the name labels under colonists.
            Type selection = AccessTools.TypeByName("RimWorld.ThingSelectionUtility");
            Patch("box selection in the isometric view", selection == null ? null : AccessTools.Method(selection, "GetMapRect"),
                postfix: nameof(GetMapRect_Postfix));
            Patch("box selection in the isometric view", selection == null ? null : AccessTools.Method(selection, "MultiSelectableThingsInScreenRectDistinct"),
                postfix: nameof(DragSelect_Postfix));
            Patch("name labels in the isometric view", AccessTools.Method(typeof(GenMapUI), "LabelDrawPosFor", new[] { typeof(Thing), typeof(float) }),
                prefix: nameof(LabelDrawPosFor_Prefix));

            Patch("mouse position", AccessTools.Method(typeof(Verse.UI), "UIToMapPosition", new[] { typeof(Vector2) }),
                prefix: nameof(UIToMapPosition_Prefix));

            Patch("visible area", AccessTools.PropertyGetter(typeof(CameraDriver), "CurrentViewRect"),
                postfix: nameof(CurrentViewRect_Postfix));

            Type thingsLayer = AccessTools.TypeByName("Verse.SectionLayer_ThingsGeneral");
            Patch("3D shapes", thingsLayer == null ? null : AccessTools.Method(thingsLayer, "TakePrintFrom"),
                prefix: nameof(TakePrintFrom_Prefix), finalizer: nameof(TakePrintFrom_Finalizer));

            bool anyPrintPlane = false;
            foreach (MethodInfo m in AccessTools.GetDeclaredMethods(typeof(Printer_Plane)))
            {
                if (m.Name == "PrintPlane" && StartsWith(m, typeof(SectionLayer), typeof(Vector3), typeof(Vector2), typeof(Material), typeof(float)))
                {
                    anyPrintPlane |= Patch("3D shapes and upright plants", m, postfix: nameof(PrintPlane_Postfix));
                }
            }
            if (!anyPrintPlane)
            {
                ModLog.Warn("[IsoRim] Printer_Plane.PrintPlane was not found in the expected form. Nothing can be raised and plants stay flat.");
            }

            Patch("lighting and fog", AccessTools.Method(typeof(SectionLayer), "DrawLayer"),
                prefix: nameof(DrawLayer_Prefix));

            try
            {
                pawnOfRenderer = AccessTools.FieldRefAccess<PawnRenderer, Pawn>("pawn");
            }
            catch (Exception)
            {
                pawnOfRenderer = null;
            }
            Patch("upright pawns", AccessTools.Method(typeof(PawnRenderer), "RenderPawnAt"),
                prefix: nameof(RenderPawnAt_Prefix), finalizer: nameof(RenderPawnAt_Finalizer));

            // The game works out each pawn's sprite layers ahead of drawing, on worker threads.
            // For a pawn the mod draws as a 3D model that work is wasted, so it is skipped.
            MethodInfo preRender = FindMethod(typeof(PawnRenderer), "ParallelPreRenderPawnAt");
            if (preRender != null)
            {
                Patch("skipping sprite work for 3D pawns", preRender, prefix: nameof(PreRender_Prefix));
            }

            // Walls, rock and trees live in the mod's own layers. Whenever one appears or goes
            // (built, deconstructed, mined, cut down) those layers are redrawn round it.
            Patch("redrawing walls and trees as they change", FindMethod(typeof(Thing), "SpawnSetup"), postfix: nameof(SpawnSetup_Postfix));
            Patch("redrawing walls and trees as they go", FindMethod(typeof(Thing), "DeSpawn"), prefix: nameof(DeSpawn_Prefix));

            // The preview of what is being placed, under the pointer.
            Type ghostDrawer = AccessTools.TypeByName("Verse.GhostDrawer");
            MethodInfo ghostThing = ghostDrawer != null ? FindMethod(ghostDrawer, "DrawGhostThing") : null;
            if (ghostThing != null && !StartsWith(ghostThing, typeof(IntVec3), typeof(Rot4), typeof(ThingDef), typeof(Graphic), typeof(Color)))
            {
                ghostThing = null;
            }
            Patch("3D placement preview", ghostThing, postfix: nameof(DrawGhostThing_Postfix));

            // The pointer in 3D: the drag box on the ground, selection brackets on the ground,
            // and clicking anywhere on a tall thing picks it.
            Patch("drag box on the ground", FindMethod(typeof(DragBox), "DragBoxOnGUI"), prefix: nameof(DragBoxOnGUI_Prefix));
            MethodInfo bracket = FindMethod(typeof(SelectionDrawer), "DrawSelectionBracketFor");
            if (bracket != null && !StartsWith(bracket, typeof(object)))
            {
                bracket = null;
            }
            Patch("selection on the ground", bracket, prefix: nameof(DrawSelectionBracketFor_Prefix));
            MethodInfo under = FindMethod(typeof(GenUI), "ThingsUnderMouse");
            if (under != null && !StartsWith(under, typeof(Vector3), typeof(float), typeof(TargetingParameters)))
            {
                under = null;
            }
            Patch("clicking on 3D shapes", under, postfix: nameof(ThingsUnderMouse_Postfix));

            // Designation icons float over what they mark (their drawing is redirected above).
            Patch("floating designation icons", FindMethod(typeof(Designation), "DesignationDraw"),
                prefix: nameof(DesignationDraw_Prefix), finalizer: nameof(Scope_Finalizer));
            Type drawBatch = AccessTools.TypeByName("Verse.DrawBatch");
            if (drawBatch != null)
            {
                foreach (MethodInfo m in AccessTools.GetDeclaredMethods(drawBatch))
                {
                    ParameterInfo[] ps = m.GetParameters();
                    if (m.Name == "DrawMesh" && ps.Length > 1 && ps[1].ParameterType == typeof(Matrix4x4) && !m.IsStatic)
                    {
                        Patch("floating batched icons", m, prefix: nameof(DrawBatch_Prefix));
                    }
                }
            }

            // The faint screen-aligned box the game draws round a designation drag is replaced by
            // one on the ground (Interaction.DrawDragBox); its measurement labels are kept.
            Patch("drag area on the ground", FindMethod(typeof(DesignationDragger), "DraggerOnGUI"),
                prefix: nameof(DraggerOnGUI_Prefix), finalizer: nameof(DraggerOnGUI_Finalizer));
            MethodInfo drawBox = AccessTools.Method(typeof(Widgets), "DrawBox", new[] { typeof(Rect), typeof(int), typeof(Texture2D) });
            Patch("drag area on the ground", drawBox, prefix: nameof(WidgetsDrawBox_Prefix));

            // The game lays dark sheets round the outside of the map to hide whatever lies past
            // its edge. In 3D they would cover the cut through the earth below the edge.
            Type clipper = AccessTools.TypeByName("Verse.MapEdgeClipDrawer");
            Patch("earth below the map edge", clipper != null ? FindMethod(clipper, "DrawClippers") : null, prefix: nameof(DrawClippers_Prefix));

            // RimWorld 1.6 draws the land around the map, flat, past the map's edges. Under the
            // tilted 3D camera that sheet shows as a smeared, flickering second map round the
            // diorama, so it is hidden while the earth edge is shown. The drawing code is found
            // by name, so nothing happens on versions that do not have it.
            int surroundHooks = 0;
            foreach (Type t in AccessTools.AllTypes())
            {
                if (t == null || t.Assembly != typeof(Map).Assembly || t.IsInterface || t.ContainsGenericParameters)
                {
                    continue;
                }
                string tn = t.Name;
                if (!(tn.Contains("Surround") || tn.Contains("OutOfBounds") || tn.Contains("BeyondMap") || tn.Contains("MapEdgeTerrain")))
                {
                    continue;
                }
                foreach (MethodInfo m in AccessTools.GetDeclaredMethods(t))
                {
                    if ((m.Name.StartsWith("Draw") || m.Name.StartsWith("Render") || m.Name == "DrawLayer") && m.ReturnType == typeof(void)
                        && !m.IsAbstract && !m.ContainsGenericParameters
                        && Patch("hiding the land past the map edge", m, prefix: nameof(Surroundings_Prefix)))
                    {
                        surroundHooks++;
                        ModLog.Debug("[IsoRim] Hiding " + t.FullName + "." + m.Name + " in 3D.");
                    }
                }
            }

            Diagnostics();

            if (surroundHooks == 0 && Prefs.DevMode)
            {
                // Lists the game's map layers, so a log from a new game version shows what to hide.
                List<string> names = new List<string>();
                foreach (Type t in typeof(SectionLayer).AllSubclassesNonAbstract())
                {
                    names.Add(t.Name);
                }
                ModLog.Warn("[IsoRim] No drawing of the land past the map edge was found. Map layers: " + string.Join(", ", names));
            }

            // The game's flat outlines of things seen through walls are made from the sprite work
            // skipped above, and do not fit 3D figures anyway, so they are left out in 3D.
            MethodInfo silhouettes = FindMethod(typeof(DynamicDrawManager), "DrawSilhouettes");
            if (silhouettes != null)
            {
                Patch("no flat silhouettes in 3D", silhouettes, prefix: nameof(DrawSilhouettes_Prefix));
            }

            // Parts the game draws every frame on top of a building (fire, charge bars, turret
            // heads) and the status icons over things have to move up with the raised sprite.
            Patch("moving parts of raised buildings", FindMethod(typeof(Thing), "DynamicDrawPhaseAt"),
                prefix: nameof(ThingDraw_Prefix), finalizer: nameof(Scope_Finalizer));

            Type overlays = AccessTools.TypeByName("RimWorld.OverlayDrawer");
            int overlayHooks = 0;
            if (overlays != null)
            {
                foreach (MethodInfo m in AccessTools.GetDeclaredMethods(overlays))
                {
                    ParameterInfo[] ps = m.GetParameters();
                    if (m.Name.StartsWith("Render") && ps.Length > 0 && ps[0].ParameterType == typeof(Thing)
                        && !m.IsAbstract && !m.ContainsGenericParameters)
                    {
                        bool hooked = m.Name.Contains("Forbidden") && !m.Name.Contains("Big") && !m.Name.Contains("Refuel")
                            ? Patch("forbidden icons", m, prefix: nameof(ForbiddenOverlay_Prefix))
                            : Patch("status icons", m, prefix: nameof(OverlayRender_Prefix), finalizer: nameof(Scope_Finalizer));
                        if (hooked)
                        {
                            overlayHooks++;
                        }
                    }
                }
            }
            if (overlayHooks == 0)
            {
                ModLog.Warn("[IsoRim] The game's status icon drawing was not found. Icons such as \"no power\" may be hidden inside raised buildings.");
            }

            Type renderUtility = AccessTools.TypeByName("Verse.PawnRenderUtility");
            MethodInfo aiming = renderUtility != null ? FindMethod(renderUtility, "DrawEquipmentAiming") : null;
            if (aiming != null && !StartsWith(aiming, typeof(Thing), typeof(Vector3), typeof(float)))
            {
                aiming = null;
            }
            Patch("3D weapons in hand", aiming, prefix: nameof(DrawEquipmentAiming_Prefix));

            // Wind turbines: the blades are a turning 3D model.
            Type wind = AccessTools.TypeByName("RimWorld.CompPowerPlantWind");
            Patch("wind turbine blades", wind == null ? null : AccessTools.DeclaredMethod(wind, "PostDraw"),
                prefix: nameof(WindPostDraw_Prefix), finalizer: nameof(WindPostDraw_Finalizer));

            // Walls are cut down in front of roofed rooms, so they have to be redrawn when a roof changes.
            Patch("cut-down walls keeping up with roofs", AccessTools.Method(typeof(RoofGrid), "SetRoof"),
                postfix: nameof(SetRoof_Postfix));

            MethodInfo movers = FindMethod(typeof(Building_Door), "DrawMovers");
            if (movers != null && !StartsWith(movers, typeof(Vector3), typeof(float)))
            {
                movers = null;
            }
            Patch("3D doors", movers, prefix: nameof(DrawMovers_Prefix));

            // Turret guns: a 3D gun turning on its 3D base.
            Type turretTop = AccessTools.TypeByName("RimWorld.TurretTop");
            if (turretTop != null)
            {
                turretParent = AccessTools.Field(turretTop, "parentTurret");
                turretRotation = AccessTools.Property(turretTop, "CurRotation");
            }
            Patch("3D turret guns", turretTop == null || turretParent == null || turretRotation == null ? null : FindMethod(turretTop, "DrawTurret"),
                prefix: nameof(DrawTurret_Prefix));

            // The buttons in the bottom right corner of the map view.
            Patch("buttons for the 3D view and roofs", AccessTools.Method(typeof(PlaySettings), "DoPlaySettingsGlobalControls"),
                postfix: nameof(PlaySettings_Postfix));

            RedirectDrawCalls();
        }

        private static FieldInfo turretParent;
        private static PropertyInfo turretRotation;

        // A turret drawing its gun. If the turret has a gun model it is drawn turned to the way the
        // gun is aiming, on top of the 3D base, and the game's flat gun is not drawn.
        public static bool DrawTurret_Prefix(object __instance)
        {
            if (!View3D.Ready || !IsoRimMod.Settings.models3D || __instance == null)
            {
                return true;
            }
            try
            {
                Thing turret = turretParent.GetValue(__instance) as Thing;
                ModelEntry entry;
                if (turret == null || !ModelLibrary.TryGet(turret.def, out entry) || entry.top == null)
                {
                    return true;
                }
                float aim = (float)turretRotation.GetValue(__instance, null);
                Vector3 at = turret.DrawPos;
                Vector3 fit = entry.Fit(turret.def) * entry.def.scale;
                DynamicModels.Draw(entry.top, new Vector3(at.x, entry.def.topHeight * fit.y, at.z), aim - 90f, fit, turret.DrawColor, R3DTextures.StuffSwatch(turret));
                return false;
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Drawing a turret's gun failed: " + e, 93611023);
                return true;
            }
        }

        // Adds the 3D view switch, and the roof switch while the 3D view is on, to the row of
        // buttons in the bottom right corner.
        public static void PlaySettings_Postfix(WidgetRow row, bool worldView)
        {
            if (worldView || row == null || Current.ProgramState != ProgramState.Playing)
            {
                return;
            }
            try
            {
                bool view = View3D.Active;
                row.ToggleableIcon(ref view, R3DIcons.View3D, "IsoRim: 3D view (" + KeyLabel(R3DKeyDefOf.R3D_ToggleView) + ")", SoundDefOf.Mouseover_ButtonToggle);
                if (view != View3D.Active)
                {
                    View3D.Active = view;
                }
                if (View3D.Active)
                {
                    bool roofs = IsoRimMod.Settings.showRoofs;
                    row.ToggleableIcon(ref roofs, R3DIcons.Roofs, "IsoRim: show roofs (" + KeyLabel(R3DKeyDefOf.R3D_ToggleRoofs) + ")", SoundDefOf.Mouseover_ButtonToggle);
                    if (roofs != IsoRimMod.Settings.showRoofs)
                    {
                        Roofs.Set(roofs);
                    }
                }
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Drawing the corner buttons failed: " + e, 93611024);
            }
        }

        private static string KeyLabel(KeyBindingDef key)
        {
            if (key == null || key.MainKey == KeyCode.None)
            {
                return "no key set";
            }
            return key.MainKeyLabel;
        }

        private static bool Patch(string feature, MethodBase target, string prefix = null, string postfix = null, string finalizer = null, string transpiler = null)
        {
            if (target == null)
            {
                ModLog.Warn("[IsoRim] The game method behind \"" + feature + "\" was not found. That part of the 3D view is off.");
                return false;
            }
            try
            {
                harmony.Patch(target, Hook(prefix), Hook(postfix), Hook(transpiler), Hook(finalizer));
                return true;
            }
            catch (Exception e)
            {
                ModLog.Warn("[IsoRim] Could not hook " + target.DeclaringType + "." + target.Name + " for \"" + feature + "\": " + e.Message);
                return false;
            }
        }

        // Looks a method up by name without throwing if the game has several with that name.
        private static MethodInfo FindMethod(Type type, string name)
        {
            try
            {
                return AccessTools.Method(type, name);
            }
            catch (Exception)
            {
                foreach (MethodInfo m in AccessTools.GetDeclaredMethods(type))
                {
                    if (m.Name == name)
                    {
                        return m;
                    }
                }
                return null;
            }
        }

        private static HarmonyMethod Hook(string name)
        {
            return name == null ? null : new HarmonyMethod(AccessTools.Method(typeof(Patches), name));
        }

        private static bool StartsWith(MethodInfo m, params Type[] types)
        {
            ParameterInfo[] ps = m.GetParameters();
            if (ps.Length < types.Length)
            {
                return false;
            }
            for (int i = 0; i < types.Length; i++)
            {
                if (ps[i].ParameterType != types[i])
                {
                    return false;
                }
            }
            return true;
        }

        // ---------------------------------------------------------------- camera

        public static void CameraUpdate_Postfix(CameraDriver __instance)
        {
            try
            {
                ApplyDrag(__instance);
                View3D.Tick();
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Camera update failed: " + e, 93611010);
            }
        }

        // The direction asked for by the movement keys and by the pointer at a screen edge:
        // x is "right", y is "up the screen".
        public static void DollyVect_Postfix(ref Vector2 __result)
        {
            if (View3D.Ready && __result != Vector2.zero)
            {
                __result = View3D.ScreenMoveToGround(__result, false);
            }
        }

        // Dragging the map with the middle mouse button. The game's own drag moves the camera
        // along the map's axes and keeps some speed after the button is let go, which goes wrong
        // with a tilted, turned camera (it used to run away into the grey beyond the map). While
        // the 3D view is on the mod does it instead: the point of ground grabbed stays under the
        // pointer, and the camera stops as soon as the button is let go.
        public static void CameraUpdate_Prefix(CameraDriver __instance)
        {
            try
            {
                if (!View3D.Ready)
                {
                    dragging = false;
                    return;
                }
                bool held = Input.GetMouseButton(2);
                if (!held)
                {
                    if (dragging)
                    {
                        dragging = false;
                        StopGameDrag(__instance);
                    }
                    return;
                }
                Camera cam = Find.Camera;
                if (cam == null)
                {
                    return;
                }
                if (!dragging)
                {
                    dragging = true;
                    dragAnchor = View3D.ScreenToGround(Input.mousePosition);
                }
                dragStartPos = cam.transform.position;
                StopGameDrag(__instance);
            }
            catch (Exception e)
            {
                dragging = false;
                Log.ErrorOnce("[IsoRim] Dragging the map failed: " + e, 93611018);
            }
        }

        private static void StopGameDrag(CameraDriver driver)
        {
            for (int i = 0; i < dragFields.Count; i++)
            {
                dragFields[i].SetValue(driver, Vector2.zero);
            }
        }

        // Called after the game's camera update: moves the camera so the grabbed ground point
        // is back under the pointer.
        private static void ApplyDrag(CameraDriver driver)
        {
            if (!dragging || !View3D.Ready || driver == null || Find.CurrentMap == null)
            {
                return;
            }
            Vector3 now = View3D.ScreenToGround(Input.mousePosition);
            Vector3 target = dragStartPos + (dragAnchor - now);
            if (float.IsNaN(target.x) || float.IsNaN(target.z) || float.IsInfinity(target.x) || float.IsInfinity(target.z))
            {
                return;
            }
            IntVec3 size = Find.CurrentMap.Size;
            target.x = Mathf.Clamp(target.x, 0f, size.x);
            target.z = Mathf.Clamp(target.z, 0f, size.z);
            driver.JumpToCurrentMapLoc(new Vector3(target.x, 0f, target.z));
        }

        // A selection box dragged on screen. The game looks for things in the block of cells
        // between two of the box's corners, which only covers the box while north is up. With
        // the camera turned the block has to reach all four corners ...
        public static void GetMapRect_Postfix(Rect __0, ref CellRect __result)
        {
            if (!View3D.Ready || View3D.Yaw == 0f)
            {
                return;
            }
            try
            {
                float scale = Prefs.UIScale;
                float h = Verse.UI.screenHeight;
                Vector3 a = View3D.ScreenToGround(new Vector2(__0.xMin, h - __0.yMin) * scale);
                Vector3 b = View3D.ScreenToGround(new Vector2(__0.xMax, h - __0.yMin) * scale);
                Vector3 c = View3D.ScreenToGround(new Vector2(__0.xMin, h - __0.yMax) * scale);
                Vector3 d = View3D.ScreenToGround(new Vector2(__0.xMax, h - __0.yMax) * scale);
                __result.minX = Mathf.FloorToInt(Mathf.Min(Mathf.Min(a.x, b.x), Mathf.Min(c.x, d.x)));
                __result.maxX = Mathf.FloorToInt(Mathf.Max(Mathf.Max(a.x, b.x), Mathf.Max(c.x, d.x)));
                __result.minZ = Mathf.FloorToInt(Mathf.Min(Mathf.Min(a.z, b.z), Mathf.Min(c.z, d.z)));
                __result.maxZ = Mathf.FloorToInt(Mathf.Max(Mathf.Max(a.z, b.z), Mathf.Max(c.z, d.z)));
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Working out a selection box failed: " + e, 93611019);
            }
        }

        // ... and what is found there is then narrowed down to what is really inside the box.
        public static IEnumerable<object> DragSelect_Postfix(IEnumerable<object> __result, Rect __0)
        {
            if (__result == null || !View3D.Ready || View3D.Yaw == 0f)
            {
                return __result;
            }
            return OnlyInsideBox(__result, __0);
        }

        private static IEnumerable<object> OnlyInsideBox(IEnumerable<object> found, Rect box)
        {
            Camera cam = Find.Camera;
            float scale = Prefs.UIScale;
            float h = Verse.UI.screenHeight;

            // Half a cell of slack, so a thing counts when the box only catches part of its cell.
            float slack = Screen.height / (2f * Mathf.Max(1f, cam.orthographicSize)) * 0.5f / scale;
            Rect grown = Rect.MinMaxRect(
                Mathf.Min(box.xMin, box.xMax) - slack, Mathf.Min(box.yMin, box.yMax) - slack,
                Mathf.Max(box.xMin, box.xMax) + slack, Mathf.Max(box.yMin, box.yMax) + slack);

            foreach (object o in found)
            {
                Thing t = o as Thing;
                if (t == null)
                {
                    yield return o;
                    continue;
                }
                Vector3 onScreen = cam.WorldToScreenPoint(t.DrawPos);
                Vector2 p = new Vector2(onScreen.x / scale, h - onScreen.y / scale);
                if (grown.Contains(p))
                {
                    yield return o;
                }
            }
        }

        // Where a thing's name label goes. The game puts it a little to the south of the thing,
        // which is "below" only while north is up. __1 is that distance (negative).
        public static bool LabelDrawPosFor_Prefix(Thing __0, float __1, ref Vector2 __result)
        {
            if (!View3D.Ready || View3D.Yaw == 0f || __0 == null)
            {
                return true;
            }
            try
            {
                Vector3 onScreen = Find.Camera.WorldToScreenPoint(__0.DrawPos + View3D.GroundForward * __1);
                float scale = Prefs.UIScale;
                __result = new Vector2(onScreen.x / scale, Verse.UI.screenHeight - onScreen.y / scale);
                return false;
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Placing a name label failed: " + e, 93611020);
                return true;
            }
        }

        // The game assumes the camera looks straight down when it turns a mouse position into a map cell.
        public static bool UIToMapPosition_Prefix(Vector2 __0, ref Vector3 __result)
        {
            if (!View3D.Ready)
            {
                return true;
            }
            __result = View3D.ScreenToGround(__0 * Prefs.UIScale);
            return false;
        }

        // Same for the area it thinks is on screen: tilted or turned, the camera sees a different part of the map.
        public static void CurrentViewRect_Postfix(ref CellRect __result)
        {
            if (View3D.Ready)
            {
                __result = View3D.GroundRect();
            }
        }

        // ---------------------------------------------------------------- static map geometry

        // Called by the game once for each non-moving thing when it rebuilds a block of the map.
        // Decides what shape the thing takes; the sprite quads it then prints are reshaped in
        // PrintPlane_Postfix.
        public static bool TakePrintFrom_Prefix(SectionLayer __instance, Thing __0)
        {
            PrintContext.Clear();
            if (!View3D.Active || __0 == null || __0.def == null)
            {
                return true;
            }

            try
            {
                // Blueprints and frames: a see-through ghost of the finished thing. A frame keeps
                // the game's sprite of the work under way beneath it.
                if (Ghosts.Target(__0) != null)
                {
                    if (Ghosts.Print(__instance, __0))
                    {
                        return __0 is Frame;
                    }
                    return true;
                }

                if (__0 is Plant)
                {
                    float rim = Forms.BaseUnder(__0, false);
                    ThingForm plantForm = Forms.For(__0.def);
                    if (plantForm.form == Form3D.Model)
                    {
                        if (SectionLayer_IsoRimTrees.Handles(__0))
                        {
                            return false;   // drawn in the mod's own tree layer
                        }
                        if (ModelBaker.Bake(__instance, __0, plantForm.model, rim))
                        {
                            return false;   // a 3D plant replaces the sprite
                        }
                    }
                    if (IsoRimMod.Settings.uprightPlants)
                    {
                        PrintContext.mode = PrintMode.Upright;
                        PrintContext.baseHeight = rim;
                    }
                    else if (rim > 0f)
                    {
                        PrintContext.mode = PrintMode.Lift;
                        PrintContext.height = rim;
                    }
                    return true;
                }

                ThingForm form = Forms.For(__0.def);
                bool item = __0.def.category == ThingCategory.Item;
                float resting = item ? Forms.BaseUnder(__0, true) : 0f;

                switch (form.form)
                {
                    case Form3D.Model:
                        if (ModelBaker.Bake(__instance, __0, form.model, resting))
                        {
                            return false;   // the model replaces the sprite
                        }
                        break;

                    case Form3D.Block:
                    {
                        if (SectionLayer_IsoRimWalls.Handles(__0))
                        {
                            return false;   // drawn in the mod's own wall layer
                        }
                        // A wall hiding a room from the camera is drawn part height.
                        float blockHeight = WallBoxes.HeightFor(__0, form.height);
                        GroundShadows.AroundBlock(__instance, __0);
                        if (IsoRimMod.Settings.texturedWalls && WallBoxes.PrintBlock(__instance, __0, blockHeight))
                        {
                            return false;   // drawn from the mod's own textures; the game's sprite is not used
                        }
                        PrintContext.mode = PrintMode.Block;
                        PrintContext.height = blockHeight;
                        break;
                    }

                    case Form3D.Extruded:
                        PrintContext.mode = PrintMode.Extrude;
                        PrintContext.baseHeight = resting;
                        PrintContext.height = resting + form.height;
                        break;

                    default:
                        if (resting > 0f)
                        {
                            PrintContext.mode = PrintMode.Lift;
                            PrintContext.height = resting;
                        }
                        break;
                }
                PrintContext.thing = __0;
                PrintContext.layer = __instance;
            }
            catch (Exception e)
            {
                PrintContext.Clear();
                Log.ErrorOnce("[IsoRim] Building 3D geometry failed: " + e, 93611011);
            }
            return true;
        }

        public static void TakePrintFrom_Finalizer()
        {
            // A wall that drew no top sprite still gets plain sides.
            if (PrintContext.mode == PrintMode.Block && !PrintContext.done && PrintContext.thing != null)
            {
                try
                {
                    WallBoxes.PrintPlainSides(PrintContext.layer, PrintContext.thing, PrintContext.height);
                }
                catch (Exception e)
                {
                    Log.ErrorOnce("[IsoRim] Building wall sides failed: " + e, 93611013);
                }
            }
            PrintContext.Clear();
        }

        // Runs after the game adds one flat sprite quad to a block's mesh.
        // __1 is the quad's centre, __2 its size, __3 its material and __4 its rotation.
        public static void PrintPlane_Postfix(SectionLayer __0, Vector3 __1, Vector2 __2, Material __3, float __4)
        {
            if (PrintContext.mode == PrintMode.None)
            {
                return;
            }
            try
            {
                PlaneHandler.Handle(__0, __1, __2, __3, __4);
            }
            catch (Exception e)
            {
                PrintContext.Clear();
                Log.ErrorOnce("[IsoRim] Reshaping a sprite failed: " + e, 93611014);
            }
        }

        // The lighting overlay and the fog of war are flat sheets. The lighting is pulled in front
        // of everything so it also darkens upright things; the fog is raised to wall height so
        // unexplored areas read as solid.
        public static bool DrawLayer_Prefix(SectionLayer __instance)
        {
            Type type = __instance.GetType();
            int kind;
            if (!layerKinds.TryGetValue(type, out kind))
            {
                string name = type.Name;
                kind = name.Contains("LightingOverlay") ? 1 : (name.Contains("FogOfWar") ? 2 : (name == "SectionLayer_BuildingsDamage" ? 3 : 0));
                layerKinds[type] = kind;
            }
            IsoRimSettings st = IsoRimMod.Settings;

            // The fog is laid over the tops of the rock and walls under it; put back flat
            // whenever the 3D view (or the setting) is off.
            if (kind == 2 && (!View3D.Ready || !st.fogLid))
            {
                if (Interaction.FogLifted(__instance))
                {
                    Interaction.LowerFog(__instance);
                }
                return true;
            }
            if (!View3D.Ready || kind == 0)
            {
                return true;
            }
            if (kind == 3)
            {
                return !st.damage3D;   // the mod's own marks are drawn on the 3D shapes instead
            }
            if (kind == 2)
            {
                try
                {
                    Interaction.LiftFog(__instance, Find.CurrentMap);
                }
                catch (Exception e)
                {
                    Log.ErrorOnce("[IsoRim] Laying the fog over the map failed: " + e, 93611160);
                }
                return true;
            }
            if (!st.lightingFix)
            {
                return true;
            }
            if (!__instance.Visible)
            {
                return false;
            }

            Matrix4x4 m = View3D.LightingMatrix;
            List<LayerSubMesh> subs = __instance.subMeshes;
            for (int i = 0; i < subs.Count; i++)
            {
                LayerSubMesh sm = subs[i];
                if (sm.finalized && !sm.disabled)
                {
                    Graphics.DrawMesh(sm.mesh, m, sm.material, 0);
                }
            }
            return false;
        }

        // ---------------------------------------------------------------- pawns

        // While a pawn is being drawn, DrawHook stands every piece of it up around its feet.
        // An animal that has a 3D model is drawn as that instead.
        // __0 is the position the pawn is drawn at.
        // Returns false (the game's own drawing of the pawn is skipped altogether) when a 3D
        // model has been drawn in its place: the game's sprite pipeline for a person is costly,
        // and skipping it rather than throwing its output away is most of what keeps a big
        // colony fast. Portraits and other off-map drawing are left to the game.
        public static bool RenderPawnAt_Prefix(PawnRenderer __instance, Vector3 __0)
        {
            DrawHook.active = false;
            DrawHook.billboard = false;
            DrawHook.skip = false;
            pawnUpright = false;
            pawnFigure = false;
            if (!View3D.Ready)
            {
                return true;
            }
            Camera current = Camera.current;
            if (current != null && current != Find.Camera)
            {
                return true;   // a portrait or some other camera: draw as usual
            }

            try
            {
                IsoRimSettings st = IsoRimMod.Settings;
                Pawn pawn = pawnOfRenderer != null ? pawnOfRenderer(__instance) : null;
                float spriteHeight = 1.5f;

                if (pawn != null && st.animals3D && st.models3D && pawn.RaceProps != null && !pawn.RaceProps.Humanlike
                    && Animals.Draw(pawn, __0))
                {
                    return false;
                }

                if (pawn != null && st.pawns3D && st.models3D && pawn.RaceProps != null && pawn.RaceProps.Humanlike)
                {
                    bool standing;
                    if (People.Draw(pawn, __0, out pawnHandHeight, out pawnFacing, out standing))
                    {
                        if (standing)
                        {
                            DrawHeldWeapon(pawn, __0, pawnHandHeight, pawnFacing);
                        }
                        return false;
                    }
                }

                if (pawn != null)
                {
                    if (pawn.Dead || pawn.GetPosture() != PawnPosture.Standing)
                    {
                        // Lying down stays flat, but is raised onto the bed if the bed has height.
                        Building_Bed bed = pawn.Dead ? null : pawn.CurrentBed();
                        float bedTop = bed != null ? Forms.HeightOf(bed) : 0f;
                        if (bedTop > 0f)
                        {
                            DrawHook.xform = View3D.LiftMatrix(bedTop);
                            DrawHook.active = true;
                        }
                        return true;
                    }

                    if (!pawn.RaceProps.Humanlike && pawn.ageTracker != null)
                    {
                        PawnKindLifeStage stage = pawn.ageTracker.CurKindLifeStage;
                        if (stage != null && stage.bodyGraphicData != null)
                        {
                            spriteHeight = stage.bodyGraphicData.drawSize.y;
                        }
                    }
                }

                if (!st.uprightPawns)
                {
                    return true;
                }

                // The feet are where the bottom of the sprite's figure is on the flat sprite. The
                // sprite is stood up about that point, then slid so the feet come down on the
                // side of the pawn's spot nearest the camera, whichever way the camera faces.
                Vector3 pivot = __0;
                pivot.z -= spriteHeight * st.feetOffset;
                Vector3 feet = __0 - View3D.GroundForward * (spriteHeight * st.feetOffset);
                DrawHook.xform = Matrix4x4.Translate(new Vector3(feet.x - pivot.x, 0f, feet.z - pivot.z)) * View3D.UprightMatrix(pivot);
                DrawHook.active = true;
                pawnUpright = true;
                pawnFeet = feet;
                pawnSize = spriteHeight / 1.5f;
            }
            catch (Exception e)
            {
                DrawHook.active = false;
            DrawHook.billboard = false;
                Log.ErrorOnce("[IsoRim] Standing a pawn upright failed: " + e, 93611012);
            }
            return true;
        }

        // True for a pawn that will certainly be drawn as a 3D model while the view is on.
        public static bool DrawnAsModel(Pawn pawn)
        {
            IsoRimSettings st = IsoRimMod.Settings;
            if (pawn == null || !View3D.Ready || !st.models3D || pawn.RaceProps == null || pawn.def == null)
            {
                return false;
            }
            if (pawn.RaceProps.Humanlike)
            {
                return st.pawns3D && pawn.def.defName == "Human" && pawn.story != null && !People.Hidden(pawn);
            }
            ModelEntry entry;
            return st.animals3D && ModelLibrary.TryGet(pawn.def, out entry) && entry.def.animal && entry.HasModel;
        }

        public static void SpawnSetup_Postfix(Thing __instance)
        {
            NoteShapeChange(__instance, __instance != null ? __instance.Map : null);
        }

        public static void DeSpawn_Prefix(Thing __instance)
        {
            NoteShapeChange(__instance, __instance != null ? __instance.MapHeld : null);
        }

        private static void NoteShapeChange(Thing t, Map map)
        {
            if (t == null || map == null || t.def == null || !View3D.Active || Current.ProgramState != ProgramState.Playing)
            {
                return;
            }
            try
            {
                if (t.def.category == ThingCategory.Building)
                {
                    if (t is Building_Door && IsoRimMod.Settings.cutRooms)
                    {
                        // A door makes (or unmakes) a room: the walls and rock in front of it may change.
                        MapSections.QueueAround(map, t.Position, WallBoxes.RockReach + 1, typeof(SectionLayer_IsoRimWalls), true);
                    }
                    if (Forms.For(t.def).form == Form3D.Block)
                    {
                        // Its own block and the ones beside it: a neighbour's side shows or hides.
                        MapSections.QueueAround(map, t.Position, WallBoxes.RockReach + 1, typeof(SectionLayer_IsoRimWalls), true);
                        if (IsoRimMod.Settings.showRoofs)
                        {
                            MapSections.QueueAround(map, t.Position, SectionLayer_IsoRimRoofs.Reach, typeof(SectionLayer_IsoRimRoofs), true);
                        }
                    }
                }
                else if (t is Plant && SectionLayer_IsoRimTrees.Handles(t))
                {
                    MapSections.QueueAround(map, t.Position, 0, typeof(SectionLayer_IsoRimTrees), true);
                }
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Noting a change to the map failed: " + e, 93611121);
            }
        }

        public static void DrawGhostThing_Postfix(IntVec3 __0, Rot4 __1, ThingDef __2, Color __4)
        {
            if (!View3D.Ready)
            {
                return;
            }
            try
            {
                Ghosts.DrawPreview(__2, __0, __1, __4);
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Drawing the placement preview failed: " + e, 93611131);
            }
        }

        private static bool inDraggerGUI;

        public static void DraggerOnGUI_Prefix()
        {
            inDraggerGUI = true;
        }

        public static void DraggerOnGUI_Finalizer()
        {
            inDraggerGUI = false;
        }

        public static bool WidgetsDrawBox_Prefix()
        {
            return !(inDraggerGUI && View3D.Ready);
        }

        public static bool DragBoxOnGUI_Prefix()
        {
            return !View3D.Ready;   // drawn on the ground instead (Interaction.DrawDragBox)
        }

        public static bool DrawSelectionBracketFor_Prefix(object __0)
        {
            Thing t = __0 as Thing;
            if (!View3D.Ready || t == null || !t.Spawned || t.Map != Find.CurrentMap)
            {
                return true;
            }
            try
            {
                Interaction.Bracket(t);
                return false;
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Drawing a selection bracket failed: " + e, 93611161);
                return true;
            }
        }

        // Puts whatever 3D shape is under the pointer first in the list of things clicked on.
        public static void ThingsUnderMouse_Postfix(TargetingParameters __2, ref List<Thing> __result)
        {
            if (!View3D.Ready || __result == null)
            {
                return;
            }
            try
            {
                List<Thing> hits = Interaction.PickUnderPointer(Find.CurrentMap);
                for (int i = hits.Count - 1; i >= 0; i--)
                {
                    Thing t = hits[i];
                    if (__2 != null && !__2.CanTarget(new TargetInfo(t)))
                    {
                        continue;
                    }
                    __result.Remove(t);
                    __result.Insert(0, t);
                }
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Picking a 3D shape under the pointer failed: " + e, 93611162);
            }
        }

        // With Development mode on, writes what the 3D view depends on to the log, so a report
        // from a new game version shows straight away what has changed.
        private static void Diagnostics()
        {
            if (!Prefs.DevMode)
            {
                return;
            }
            try
            {
                Material solid = R3DMaterials.Solid;
                Shader cutout = ShaderDatabase.Cutout;
                ModLog.Warn("[IsoRim] Diagnostics: game " + VersionControl.CurrentVersionStringWithRev
                    + " | solid shader " + (solid != null && solid.shader != null ? solid.shader.name : "MISSING")
                    + " (has _Color " + (solid != null && solid.HasProperty("_Color")) + ")"
                    + " | cutout shader " + (cutout != null ? cutout.name : "MISSING")
                    + " | game shadow material " + (R3DMaterials.GameShadow != null ? R3DMaterials.GameShadow.shader.name : "MISSING"));
                List<string> layers = new List<string>();
                foreach (Type t in typeof(SectionLayer).AllSubclassesNonAbstract())
                {
                    layers.Add(t.Name);
                }
                ModLog.Warn("[IsoRim] Diagnostics: map layers: " + string.Join(", ", layers));
            }
            catch (Exception e)
            {
                ModLog.Warn("[IsoRim] Diagnostics failed: " + e.Message);
            }
        }

        public static bool Surroundings_Prefix()
        {
            return !(View3D.Ready && IsoRimMod.Settings.mapEdge3D);
        }

        public static bool DrawClippers_Prefix()
        {
            return !(View3D.Ready && IsoRimMod.Settings.mapEdge3D);
        }

        public static bool DrawSilhouettes_Prefix()
        {
            return !View3D.Ready;
        }

        public static bool PreRender_Prefix(PawnRenderer __instance)
        {
            try
            {
                // Only people: the game still uses an animal's prepared sprite in a few places
                // the mod does not take over (the sprite then came out garbled when the animal
                // turned), and animals are cheap to prepare anyway.
                Pawn pawn = pawnOfRenderer != null ? pawnOfRenderer(__instance) : null;
                if (pawn == null || pawn.RaceProps == null || !pawn.RaceProps.Humanlike)
                {
                    return true;
                }
                return !DrawnAsModel(pawn);
            }
            catch (Exception)
            {
                return true;
            }
        }

        // The weapon of a 3D figure, drawn here because the game's own drawing (which would
        // otherwise do it) is skipped. Shown when the person is drafted or aiming, pointed at
        // what they are aiming at, otherwise the way they face.
        private static void DrawHeldWeapon(Pawn pawn, Vector3 feet, float handHeight, float facing)
        {
            IsoRimSettings st = IsoRimMod.Settings;
            if (!st.heldWeapons3D || pawn.equipment == null || pawn.equipment.Primary == null)
            {
                return;
            }
            Thing weapon = pawn.equipment.Primary;
            float aim = facing;
            bool aiming = false;
            Stance_Busy busy = pawn.stances != null ? pawn.stances.curStance as Stance_Busy : null;
            if (busy != null && busy.focusTarg.IsValid)
            {
                Vector3 to = busy.focusTarg.HasThing ? busy.focusTarg.Thing.DrawPos : busy.focusTarg.Cell.ToVector3Shifted();
                to -= pawn.DrawPos;
                if (to.x * to.x + to.z * to.z > 0.001f)
                {
                    aim = to.AngleFlat();
                    aiming = true;
                }
            }
            if (!aiming && !pawn.Drafted)
            {
                return;
            }
            float artYaw = aim - 90f;
            Vector3 artDir = Quaternion.AngleAxis(artYaw, Vector3.up) * Vector3.right;
            if (st.itemsFromArt && SpriteSolids.DrawHeld(weapon,
                new Vector3(feet.x + artDir.x * 0.30f, handHeight, feet.z + artDir.z * 0.30f), aim))
            {
                return;
            }
            ModelEntry entry;
            if (!ModelLibrary.TryGet(weapon.def, out entry) || !entry.HasModel)
            {
                return;
            }
            float yaw = aim - 90f;
            Vector3 dir = Quaternion.AngleAxis(yaw, Vector3.up) * Vector3.right;
            Vector3 hand = new Vector3(0f, handHeight, 0f) + dir * 0.30f;
            DynamicModels.Draw(entry.Pick(weapon), new Vector3(feet.x + hand.x, hand.y, feet.z + hand.z), yaw, Vector3.one * entry.def.scale,
                weapon.DrawColor, R3DTextures.StuffSwatch(weapon));
        }

        public static void RenderPawnAt_Finalizer()
        {
            DrawHook.active = false;
            DrawHook.billboard = false;
            DrawHook.skip = false;
            pawnFigure = false;
            pawnUpright = false;
        }

        // The weapon in a standing pawn's hands. __0 is the weapon and __2 the direction it
        // points, in degrees clockwise from north. If the weapon has a model it is drawn as a
        // real object lying level and pointing that way, at the place on the pawn's sprite
        // where its hands are; otherwise the game draws its usual sprite.
        public static bool DrawEquipmentAiming_Prefix(Thing __0, float __2)
        {
            if ((!pawnUpright && !pawnFigure) || __0 == null || !View3D.Ready)
            {
                return true;
            }
            try
            {
                IsoRimSettings st = IsoRimMod.Settings;
                if (!st.heldWeapons3D)
                {
                    return true;
                }
                float yaw = __2 - 90f;
                Vector3 aim = Quaternion.AngleAxis(yaw, Vector3.up) * Vector3.right;
                // A flat sprite holds it part of the way up the sprite; a 3D figure at its side.
                Vector3 hand = pawnFigure
                    ? new Vector3(0f, pawnHandHeight, 0f) + aim * 0.30f
                    : View3D.CardUp * (HandHeight * pawnSize) + aim * HandReach;
                Vector3 position = new Vector3(pawnFeet.x + hand.x, hand.y, pawnFeet.z + hand.z);
                if (st.itemsFromArt && SpriteSolids.DrawHeld(__0, position, __2))
                {
                    return false;
                }
                ModelEntry entry;
                if (!st.models3D || !ModelLibrary.TryGet(__0.def, out entry) || !entry.HasModel)
                {
                    return true;
                }
                DynamicModels.Draw(entry.Pick(__0), position, yaw, Vector3.one * entry.def.scale, __0.DrawColor, R3DTextures.StuffSwatch(__0));
                return false;
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Drawing a held weapon failed: " + e, 93611016);
                return true;
            }
        }

        // A wind turbine drawing its blades. If the turbine has a 3D model, a turning 3D rotor is
        // drawn and the game's flat blades are thrown away.
        public static void WindPostDraw_Prefix(ThingComp __instance, out bool __state)
        {
            __state = false;
            if (!View3D.Ready)
            {
                return;
            }
            try
            {
                if (Turbines.Draw(__instance))
                {
                    __state = true;
                    DrawHook.skip = true;
                }
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Drawing a wind turbine's blades failed: " + e, 93611021);
            }
        }

        public static void WindPostDraw_Finalizer(bool __state)
        {
            if (__state)
            {
                DrawHook.skip = false;
            }
        }

        // A roof was added or removed at __0.
        public static void SetRoof_Postfix(RoofGrid __instance, IntVec3 __0)
        {
            IsoRimSettings st = IsoRimMod.Settings;
            if (!View3D.Active || (!st.cutRooms && !st.showRoofs) || Current.ProgramState != ProgramState.Playing)
            {
                return;
            }
            try
            {
                List<Map> maps = Find.Maps;
                for (int i = 0; i < maps.Count; i++)
                {
                    if (maps[i].roofGrid == __instance)
                    {
                        if (st.cutRooms)
                        {
                            Cutaway.RoofChanged(maps[i], __0);
                            if (st.cutRock)
                            {
                                MapSections.QueueAround(maps[i], __0, WallBoxes.RockReach + 1, typeof(SectionLayer_IsoRimWalls), true);
                            }
                        }
                        if (st.showRoofs)
                        {
                            // A roof's slopes are worked out from the cells around it, so the
                            // blocks next door may need their part of the roof redrawn too.
                            MapSections.QueueAround(maps[i], __0, SectionLayer_IsoRimRoofs.Reach, typeof(SectionLayer_IsoRimRoofs));
                        }
                        break;
                    }
                }
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Noting a roof change failed: " + e, 93611022);
            }
        }

        // The sliding leaves of a door. __1 is how far they have slid open.
        public static bool DrawMovers_Prefix(Building_Door __instance, float __1)
        {
            if (!View3D.Ready || __instance == null || !IsoRimMod.Settings.doors3D)
            {
                return true;
            }
            try
            {
                if (__instance.def.size.x != 1 || __instance.def.size.z != 1)
                {
                    return true;   // wide doors keep the game's drawing for now
                }
                return !Doors.Draw(__instance, __1);
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Drawing a door failed: " + e, 93611017);
                return true;
            }
        }

        // ---------------------------------------------------------------- raised things

        // What DrawHook was doing before a scope started, so it can be put back afterwards.
        public struct DrawScope
        {
            public bool changed;
            public bool wasActive;
            public Matrix4x4 wasXform;
            public bool wasBillboard;
            public float wasHeight;
            public bool wasAnchored;
            public Vector3 wasAnchor;
        }

        // Wraps the game's per-frame drawing of one thing. __0 is the drawing phase; only the
        // final phase runs on the main thread and actually draws.
        public static void ThingDraw_Prefix(Thing __instance, DrawPhase __0, out DrawScope __state)
        {
            __state = default(DrawScope);
            if (__0 != DrawPhase.Draw || !View3D.Ready || __instance == null || __instance is Pawn)
            {
                return;
            }
            // Speech bubbles and icons over people's heads stand up and float above them.
            Mote mote = __instance as Mote;
            if (mote != null && (mote.def.altitudeLayer == AltitudeLayer.MetaOverlays || mote.def.altitudeLayer == AltitudeLayer.MoteOverhead))
            {
                BeginBillboard(ref __state, OverheadHeight, false, Vector3.zero);
                return;
            }
            BeginLift(__instance, ref __state);
        }

        private const float OverheadHeight = 1.45f;   // above a standing colonist's head, in cells
        private const float IconGap = 0.30f;          // how far above a thing its icons float

        // Stands every mesh drawn until the scope ends upright, facing the camera, raised by height cells.
        // With anchored, the icons gather over anchor (see DrawHook.hasAnchor) and bob gently,
        // like the diamond over a Sim's head.
        private static void BeginBillboard(ref DrawScope state, float height, bool anchored, Vector3 anchor)
        {
            if (DrawHook.active)
            {
                return;
            }
            state.changed = true;
            state.wasActive = DrawHook.active;
            state.wasXform = DrawHook.xform;
            state.wasBillboard = DrawHook.billboard;
            state.wasHeight = DrawHook.billboardHeight;
            state.wasAnchored = DrawHook.hasAnchor;
            state.wasAnchor = DrawHook.billboardAnchor;
            if (anchored)
            {
                height += 0.05f * Mathf.Sin(Time.realtimeSinceStartup * 2.4f + anchor.x * 1.3f + anchor.z * 0.7f);
            }
            DrawHook.billboard = true;
            DrawHook.billboardHeight = height;
            DrawHook.hasAnchor = anchored;
            DrawHook.billboardAnchor = anchor;
            DrawHook.active = true;
        }

        private static Material forbiddenMat;
        private static bool forbiddenLooked;

        // The forbidden cross: the game may draw it in a batch the mod cannot reach, so in 3D
        // it is drawn here instead, upright over the thing.
        public static bool ForbiddenOverlay_Prefix(Thing __0)
        {
            if (!View3D.Ready || __0 == null || __0 is Pawn)
            {
                return true;
            }
            try
            {
                if (!forbiddenLooked)
                {
                    forbiddenLooked = true;
                    Type overlays = AccessTools.TypeByName("RimWorld.OverlayDrawer");
                    FieldInfo f = overlays != null ? AccessTools.Field(overlays, "ForbiddenMat") : null;
                    forbiddenMat = f != null ? f.GetValue(null) as Material : null;
                }
                if (forbiddenMat == null)
                {
                    return true;
                }
                DrawScope scope = default(DrawScope);
                Vector3 at = __0.TrueCenter();
                BeginBillboard(ref scope, Interaction.PickHeight(__0) + IconGap, true, at);
                DrawHook.DrawMesh(MeshPool.plane05, Matrix4x4.TRS(new Vector3(at.x, AltitudeLayer.MetaOverlays.AltitudeFor(), at.z), Quaternion.identity, Vector3.one), forbiddenMat, 0);
                Scope_Finalizer(scope);
                return false;
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Drawing a forbidden icon failed: " + e, 93611171);
                return true;
            }
        }

        // A designation (mine, haul, cut, deconstruct ...): its icon floats over what it marks.
        public static void DesignationDraw_Prefix(Designation __instance, out DrawScope __state)
        {
            __state = default(DrawScope);
            if (!View3D.Ready || __instance == null)
            {
                return;
            }
            try
            {
                float h = 0f;
                LocalTargetInfo target = __instance.target;
                Map map = __instance.designationManager != null ? __instance.designationManager.map : Find.CurrentMap;
                if (target.HasThing)
                {
                    h = Interaction.PickHeight(target.Thing);
                }
                else if (target.Cell.IsValid && map != null)
                {
                    h = WallBoxes.BlockHeightAt(map, target.Cell);
                    Building b = target.Cell.InBounds(map) ? target.Cell.GetEdifice(map) : null;
                    if (b != null)
                    {
                        h = Mathf.Max(h, Interaction.PickHeight(b));
                    }
                }
                Vector3 anchor = target.HasThing ? target.Thing.TrueCenter() : target.Cell.ToVector3Shifted();
                BeginBillboard(ref __state, h + IconGap, true, anchor);
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Raising a designation icon failed: " + e, 93611170);
            }
        }

        // The game also draws some icons in batches; the same transform is applied there.
        public static bool DrawBatch_Prefix(ref Matrix4x4 __1)
        {
            if (!DrawHook.active)
            {
                return true;
            }
            if (DrawHook.skip)
            {
                return false;
            }
            __1 = DrawHook.Transform(__1);
            return true;
        }

        // Wraps the drawing of one status icon. __0 is the thing the icon belongs to.
        public static void OverlayRender_Prefix(Thing __0, out DrawScope __state)
        {
            __state = default(DrawScope);
            if (!View3D.Ready || __0 == null || __0 is Pawn)
            {
                return;
            }
            // Status icons (no power, forbidden, out of fuel ...) stand up and float above the thing.
            float h = 0f;
            try
            {
                h = Interaction.PickHeight(__0);
            }
            catch (Exception)
            {
            }
            BeginBillboard(ref __state, h + IconGap, true, __0.TrueCenter());
        }

        public static void Scope_Finalizer(DrawScope __state)
        {
            if (__state.changed)
            {
                DrawHook.active = __state.wasActive;
                DrawHook.xform = __state.wasXform;
                DrawHook.billboard = __state.wasBillboard;
                DrawHook.billboardHeight = __state.wasHeight;
                DrawHook.hasAnchor = __state.wasAnchored;
                DrawHook.billboardAnchor = __state.wasAnchor;
            }
        }

        private static void BeginLift(Thing t, ref DrawScope state)
        {
            // Already inside another scope, such as an item in a pawn's hands: leave that in charge.
            if (DrawHook.active)
            {
                return;
            }
            try
            {
                float h = Forms.HeightOf(t);
                if (h <= 0f)
                {
                    return;
                }
                state.changed = true;
                state.wasActive = DrawHook.active;
                state.wasXform = DrawHook.xform;
                DrawHook.xform = View3D.LiftMatrix(h);
                DrawHook.active = true;
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Raising a thing's moving parts failed: " + e, 93611015);
            }
        }

        // Finds every method in the pawn drawing code that hands a mesh to Unity and points it at
        // DrawHook instead. Shadows are left out so they stay on the ground.
        private static void RedirectDrawCalls()
        {
            List<Type> types = new List<Type>();
            AddTypeAndSubclasses(types, "Verse.PawnRenderer");
            AddTypeAndSubclasses(types, "Verse.PawnRenderTree");
            AddTypeAndSubclasses(types, "Verse.PawnRenderUtility");
            AddTypeAndSubclasses(types, "Verse.PawnRenderNodeWorker");
            AddTypeAndSubclasses(types, "Verse.Graphic");
            AddTypeAndSubclasses(types, "RimWorld.OverlayDrawer");
            AddTypeAndSubclasses(types, "RimWorld.TurretTop");
            AddTypeAndSubclasses(types, "RimWorld.CompPowerPlantWind");
            AddTypeAndSubclasses(types, "Verse.Designation");

            HarmonyMethod transpiler = Hook(nameof(Redirect_Transpiler));
            int count = 0;

            foreach (Type type in types)
            {
                if (type.ContainsGenericParameters || type.Name.Contains("Shadow"))
                {
                    continue;
                }
                foreach (MethodInfo m in AccessTools.GetDeclaredMethods(type))
                {
                    if (TryRedirect(m, transpiler))
                    {
                        count++;
                    }
                }
            }

            foreach (MethodInfo m in AccessTools.GetDeclaredMethods(typeof(GenDraw)))
            {
                if ((m.Name == "DrawMeshNowOrLater" || m.Name == "DrawFillableBar") && TryRedirect(m, transpiler))
                {
                    count++;
                }
            }

            if (count == 0)
            {
                ModLog.Warn("[IsoRim] No drawing code could be redirected, so pawns will stay flat.");
            }
            else
            {
                ModLog.Debug("[IsoRim] Drawing redirected in " + count + " methods.");
            }
        }

        private static void AddTypeAndSubclasses(List<Type> types, string typeName)
        {
            Type type = AccessTools.TypeByName(typeName);
            if (type == null)
            {
                return;
            }
            types.Add(type);
            foreach (Type sub in type.AllSubclasses())
            {
                types.Add(sub);
            }
        }

        private static bool TryRedirect(MethodInfo m, HarmonyMethod transpiler)
        {
            try
            {
                if (m.IsAbstract || m.ContainsGenericParameters || m.GetMethodBody() == null)
                {
                    return false;
                }
                if (m.Name.Contains("Shadow") || m.Name.Contains("Debug"))
                {
                    return false;
                }

                bool draws = false;
                foreach (KeyValuePair<OpCode, object> instruction in PatchProcessor.ReadMethodBody(m))
                {
                    if (IsRedirectable(instruction.Value as MethodInfo))
                    {
                        draws = true;
                        break;
                    }
                }
                if (!draws)
                {
                    return false;
                }

                harmony.Patch(m, null, null, transpiler, null);
                return true;
            }
            catch (Exception e)
            {
                ModLog.Warn("[IsoRim] Could not redirect drawing in " + m.DeclaringType + "." + m.Name + ": " + e.Message);
                return false;
            }
        }

        private static bool IsRedirectable(MethodInfo callee)
        {
            return callee != null
                && callee.DeclaringType == typeof(Graphics)
                && callee.Name == "DrawMesh"
                && DrawHook.ReplacementFor(callee) != null;
        }

        public static IEnumerable<CodeInstruction> Redirect_Transpiler(IEnumerable<CodeInstruction> instructions)
        {
            foreach (CodeInstruction ci in instructions)
            {
                if (ci.opcode == OpCodes.Call)
                {
                    MethodInfo callee = ci.operand as MethodInfo;
                    if (IsRedirectable(callee))
                    {
                        ci.operand = DrawHook.ReplacementFor(callee);
                    }
                }
                yield return ci;
            }
        }
    }
}
