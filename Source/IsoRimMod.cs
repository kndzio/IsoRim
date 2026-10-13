using System;
using System.Collections.Generic;
using System.Reflection;
using RimWorld;
using UnityEngine;
using Verse;

namespace IsoRim
{
    public class IsoRimSettings : ModSettings
    {
        public float pitch = 55f;        // camera angle in degrees; 90 looks straight down
        public bool isometric = true;    // camera turned 45 degrees and lowered, as in isometric games
        public float isoPitch = 35.3f;   // camera angle while isometric; 35.3 is the true isometric angle
        public float wallHeight = 1.2f;    // height of a full wall, in cells
        public float squash = 0.003f;    // how far the game's flat draw layers are pressed together
        public float feetOffset = 0.3f;  // where a pawn's feet sit, as a fraction of sprite height below centre
        public float saturation = 0.85f; // custom look: how much of the colour is kept (1 = untouched)
        public float brightness = 0.95f; // custom look: how much of the brightness is kept (1 = untouched)
        public float treeShadowLength = 0.2f;   // shadow height per cell of tree, on the game's scale where a wall is 1
        public float cutHeight = 0.5f;   // how much is left of a wall that is cut down to show the room behind
        public float dissolveRadius = 3.5f; // radius around the mouse cursor within which walls are cut down

        public bool uprightPawns = true;
        public bool uprightPlants = true;
        public bool walls3D = true;
        public bool texturedWalls = true;
        public bool autoExtrude = true;
        public bool thickItems = true;
        public bool itemsFromArt = true;
        public bool ghosts3D = true;
        public bool cutRock = true;
        public bool mapEdge3D = true;
        public float itemThickness = 1f;
        public bool workAnimations = true;
        public bool damage3D = true;
        public bool outlines = true;
        public bool texturedModels = true;
        public bool ruggedRock = true;
        public bool trees3D = true;
        public bool smallPlants3D = true;
        public bool groundStyle = true;
        public bool grassSoil = true;
        public bool floorStyle = true;
        public bool waterStyle = true;   // the mod's own stylised water
        public bool cutHover = true;     // walls under the pointer are cut down
        public bool cutRooms = false;    // walls in front of every roofed room are cut down
        public int turn = 0;             // eighth turns of the camera, clockwise
        public bool snap45 = true;       // Q and E turn an eighth (45 degrees) at a time; otherwise a quarter
        public bool pawns3D = true;
        public bool effects3D = true;
        public bool groundShadows = true;
        public bool treeShadows = true;
        public bool grade = true;        // colour grade on
        public string lookName = "Gentle";
        public float lookStrength = 1f;
        public bool useLut = true;       // use the exact LUT for a look when the shader bundle is installed
        public string lutFile = "";      // a LUT file picked by name instead of a look's own
        public bool animals3D = true;
        public bool heldWeapons3D = true;
        public bool doors3D = true;
        public bool models3D = true;
        public bool lightingFix = true;
        public bool fogLid = true;
        public bool showRoofs = false;
        public int roofStyle = 0;        // slate, terracotta, thatch, tin
        public bool sunMoves = true;
        public bool cutFrontOnly = false;        // only walls between the camera and the pointer are lowered
        public bool cutNearColonists = false;    // walls round colonists are lowered too
        public float colonistRadius = 2.5f;
        public bool treesNearPointer = true;     // trees near the pointer drop their leaves so what is under them shows
        public bool treesNearColonists = false;
        public float treeRadius = 2.5f;
        public bool roofHover = true;            // the roof of the room under the pointer is lifted off
        public bool roofOverColonists = false;   // and of every room a colonist is in     // the sun crosses the sky through the day; otherwise it stays put

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref pitch, "pitch", 55f);
            Scribe_Values.Look(ref isometric, "isometric", true);
            Scribe_Values.Look(ref isoPitch, "isoPitch", 35.3f);
            Scribe_Values.Look(ref wallHeight, "wallHeight", 1.2f);
            Scribe_Values.Look(ref squash, "squash", 0.02f);
            Scribe_Values.Look(ref feetOffset, "feetOffset", 0.3f);
            Scribe_Values.Look(ref saturation, "saturation", 0.85f);
            Scribe_Values.Look(ref brightness, "brightness", 0.95f);
            Scribe_Values.Look(ref treeShadowLength, "treeShadowLength", 0.2f);
            Scribe_Values.Look(ref uprightPawns, "uprightPawns", true);
            Scribe_Values.Look(ref uprightPlants, "uprightPlants", true);
            Scribe_Values.Look(ref walls3D, "walls3D", true);
            Scribe_Values.Look(ref texturedWalls, "texturedWalls", true);
            Scribe_Values.Look(ref autoExtrude, "autoExtrude", true);
            Scribe_Values.Look(ref thickItems, "thickItems", true);
            Scribe_Values.Look(ref itemsFromArt, "itemsFromArt", true);
            Scribe_Values.Look(ref ghosts3D, "ghosts3D", true);
            Scribe_Values.Look(ref cutRock, "cutRock", true);
            Scribe_Values.Look(ref mapEdge3D, "mapEdge3D", true);
            Scribe_Values.Look(ref itemThickness, "itemThickness", 1f);
            Scribe_Values.Look(ref workAnimations, "workAnimations", true);
            Scribe_Values.Look(ref damage3D, "damage3D", true);
            Scribe_Values.Look(ref outlines, "outlines", true);
            Scribe_Values.Look(ref texturedModels, "texturedModels", true);
            Scribe_Values.Look(ref ruggedRock, "ruggedRock", true);
            Scribe_Values.Look(ref trees3D, "trees3D", true);
            Scribe_Values.Look(ref smallPlants3D, "smallPlants3D", true);
            Scribe_Values.Look(ref groundStyle, "groundStyle", true);
            Scribe_Values.Look(ref grassSoil, "grassSoil", true);
            Scribe_Values.Look(ref floorStyle, "floorStyle", true);
            Scribe_Values.Look(ref waterStyle, "waterStyle", true);
            Scribe_Values.Look(ref cutHover, "cutHover", true);
            Scribe_Values.Look(ref cutRooms, "cutRooms", false);
            Scribe_Values.Look(ref turn, "turnSteps", 0);
            Scribe_Values.Look(ref snap45, "snap45", true);
            Scribe_Values.Look(ref pawns3D, "pawns3D", true);
            Scribe_Values.Look(ref effects3D, "effects3D", true);
            Scribe_Values.Look(ref cutHeight, "cutHeight", 0.5f);
            Scribe_Values.Look(ref dissolveRadius, "dissolveRadius", 3.5f);
            Scribe_Values.Look(ref groundShadows, "groundShadows", true);
            Scribe_Values.Look(ref treeShadows, "treeShadows", true);
            Scribe_Values.Look(ref grade, "grade", true);
            Scribe_Values.Look(ref lookName, "lookName", "Gentle");
            Scribe_Values.Look(ref lookStrength, "lookStrength", 1f);
            Scribe_Values.Look(ref useLut, "useLut", true);
            Scribe_Values.Look(ref lutFile, "lutFile", "");
            Scribe_Values.Look(ref animals3D, "animals3D", true);
            Scribe_Values.Look(ref heldWeapons3D, "heldWeapons3D", true);
            Scribe_Values.Look(ref doors3D, "doors3D", true);
            Scribe_Values.Look(ref models3D, "models3D", true);
            Scribe_Values.Look(ref lightingFix, "lightingFix", true);
            Scribe_Values.Look(ref fogLid, "fogLid", true);
            Scribe_Values.Look(ref showRoofs, "showRoofs", false);
            Scribe_Values.Look(ref roofStyle, "roofStyle", 0);
            Scribe_Values.Look(ref sunMoves, "sunMoves", true);
            Scribe_Values.Look(ref cutFrontOnly, "cutFrontOnly", false);
            Scribe_Values.Look(ref cutNearColonists, "cutNearColonists", false);
            Scribe_Values.Look(ref colonistRadius, "colonistRadius", 2.5f);
            Scribe_Values.Look(ref treesNearPointer, "treesNearPointer", true);
            Scribe_Values.Look(ref treesNearColonists, "treesNearColonists", false);
            Scribe_Values.Look(ref treeRadius, "treeRadius", 2.5f);
            Scribe_Values.Look(ref roofHover, "roofHover", true);
            Scribe_Values.Look(ref roofOverColonists, "roofOverColonists", false);
            if (lookName == null)
            {
                lookName = "Gentle";
            }
            if (lutFile == null)
            {
                lutFile = "";
            }
        }

        // Puts every option back to its default.
        public void Reset()
        {
            IsoRimSettings fresh = new IsoRimSettings();
            foreach (FieldInfo f in typeof(IsoRimSettings).GetFields(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            {
                f.SetValue(this, f.GetValue(fresh));
            }
        }
    }

    public class IsoRimMod : Mod
    {
        public static IsoRimSettings Settings;
        public static string RootDir;   // this mod's folder
        private static IsoRimMod instance;

        public IsoRimMod(ModContentPack content) : base(content)
        {
            instance = this;
            Settings = GetSettings<IsoRimSettings>();
            RootDir = content.RootDir;
        }

        // Writes the options to disk now (they are also written when the options window closes).
        public static void Save()
        {
            if (instance != null)
            {
                instance.WriteSettings();
            }
        }

        public override string SettingsCategory()
        {
            return "IsoRim";
        }

        public override void DoSettingsWindowContents(Rect inRect)
        {
            SettingsWindow.Draw(inRect, Settings);
        }
    }

    // The options screen: a header with the main switch, then four tabs, each in two columns of
    // titled sections.
    public static class SettingsWindow
    {
        private static int tab;
        private static readonly Color Muted = new Color(0.72f, 0.72f, 0.72f);
        private static readonly Color Rule = new Color(1f, 1f, 1f, 0.18f);
        private static readonly Color Accent = new Color(0.55f, 0.78f, 0.95f);
        private static readonly Color[] Palette =
        {
            new Color(0.42f, 0.55f, 0.30f), new Color(0.55f, 0.42f, 0.30f), new Color(0.58f, 0.57f, 0.55f), new Color(0.30f, 0.50f, 0.60f),
            new Color(0.88f, 0.70f, 0.58f), new Color(0.86f, 0.88f, 0.92f), new Color(0.72f, 0.22f, 0.20f), new Color(0.18f, 0.17f, 0.16f),
        };

        public static void Draw(Rect inRect, IsoRimSettings st)
        {
            Text.Font = GameFont.Small;
            Rect header = new Rect(inRect.x, inRect.y, inRect.width, 52f);
            Header(header, st);

            Rect body = new Rect(inRect.x, header.yMax + 36f, inRect.width, inRect.height - header.height - 36f);
            List<TabRecord> tabs = new List<TabRecord>
            {
                new TabRecord("View and camera", delegate { tab = 0; }, tab == 0),
                new TabRecord("See-through", delegate { tab = 4; }, tab == 4),
                new TabRecord("Colour and light", delegate { tab = 1; }, tab == 1),
                new TabRecord("Ground, water, roofs", delegate { tab = 2; }, tab == 2),
                new TabRecord("What is 3D", delegate { tab = 3; }, tab == 3),
            };
            Widgets.DrawMenuSection(body);
            TabDrawer.DrawTabs(body, tabs);

            Rect inner = body.ContractedBy(14f);
            float gap = 24f;
            float colW = (inner.width - gap) / 2f;
            Rect left = new Rect(inner.x, inner.y, colW, inner.height);
            Rect right = new Rect(inner.x + colW + gap, inner.y, colW, inner.height);
            GUI.color = Rule;
            Widgets.DrawLineVertical(inner.x + colW + gap / 2f, inner.y, inner.height);
            GUI.color = Color.white;

            // One column at a time: a listing opens a drawing group, and two open at once would
            // nest, putting everything in the second outside the first and drawing nothing.
            Listing_Standard l = new Listing_Standard();
            l.Begin(left);
            Tab(l, null, st);
            l.End();
            Listing_Standard r = new Listing_Standard();
            r.Begin(right);
            Tab(null, r, st);
            r.End();
            Text.Font = GameFont.Small;
            Text.Anchor = TextAnchor.UpperLeft;
            GUI.color = Color.white;
        }

        // ---------------------------------------------------------------- header

        private static void Header(Rect rect, IsoRimSettings st)
        {
            Widgets.DrawBoxSolid(rect, new Color(0.10f, 0.12f, 0.14f, 0.65f));
            GUI.color = Accent;
            Widgets.DrawBoxSolid(new Rect(rect.x, rect.y, 4f, rect.height), Accent);
            GUI.color = Color.white;

            Text.Anchor = TextAnchor.MiddleLeft;
            Text.Font = GameFont.Small;
            GUI.color = Muted;
            string status = (View3D.Active ? "3D view is on" : "3D view is off")
                + "   ·   camera turns " + (st.snap45 ? "45°" : "90°") + " a step";
            Widgets.Label(new Rect(rect.x + 16f, rect.y, rect.width - 300f, rect.height), status);
            GUI.color = Color.white;
            Text.Font = GameFont.Small;
            Text.Anchor = TextAnchor.UpperLeft;

            Rect toggle = new Rect(rect.xMax - 270f, rect.y + 11f, 150f, 30f);
            if (Widgets.ButtonText(toggle, View3D.Active ? "Turn 3D view off" : "Turn 3D view on"))
            {
                View3D.Active = !View3D.Active;
            }
            Rect reset = new Rect(rect.xMax - 110f, rect.y + 11f, 100f, 30f);
            if (Widgets.ButtonText(reset, "Reset all"))
            {
                Find.WindowStack.Add(Dialog_MessageBox.CreateConfirmation("Put every IsoRim option back to its default?", delegate
                {
                    bool roofs = st.showRoofs;
                    st.Reset();
                    if (roofs != st.showRoofs)
                    {
                        st.showRoofs = roofs;
                        Roofs.Set(!roofs);
                    }
                }));
            }
        }

        // ---------------------------------------------------------------- building blocks

        private static void Section(Listing_Standard l, string title, string note = null)
        {
            if (l.CurHeight > 1f)
            {
                l.Gap(10f);
            }
            Text.Font = GameFont.Medium;
            Rect r = l.GetRect(30f);
            Widgets.Label(r, title);
            Text.Font = GameFont.Small;
            GUI.color = Rule;
            Widgets.DrawLineHorizontal(r.x, r.yMax - 1f, r.width);
            GUI.color = Color.white;
            if (note != null)
            {
                Text.Font = GameFont.Tiny;
                GUI.color = Muted;
                l.Label(note);
                GUI.color = Color.white;
                Text.Font = GameFont.Small;
            }
            l.Gap(4f);
        }

        private static void Note(Listing_Standard l, string text)
        {
            Text.Font = GameFont.Tiny;
            GUI.color = Muted;
            l.Label(text);
            GUI.color = Color.white;
            Text.Font = GameFont.Small;
        }

        private static float Slider(Listing_Standard l, string label, float value, float min, float max, string shown, string tip = null)
        {
            Rect r = l.GetRect(22f);
            Widgets.Label(r.LeftPart(0.72f), label);
            Text.Anchor = TextAnchor.MiddleRight;
            GUI.color = Accent;
            Widgets.Label(r.RightPart(0.28f), shown);
            GUI.color = Color.white;
            Text.Anchor = TextAnchor.UpperLeft;
            if (tip != null)
            {
                TooltipHandler.TipRegion(r, tip);
            }
            return l.Slider(value, min, max);
        }

        private static void Check(Listing_Standard l, string label, ref bool value, string tip = null)
        {
            l.CheckboxLabeled(label, ref value, tip);
        }

        private static string KeyOf(KeyBindingDef key)
        {
            if (key == null || key.MainKey == KeyCode.None)
            {
                return "-";
            }
            return key.MainKeyLabel;
        }

        private static void KeyRow(Listing_Standard l, KeyBindingDef key, string what)
        {
            Rect r = l.GetRect(22f);
            GUI.color = Accent;
            Widgets.Label(r.LeftPart(0.22f), KeyOf(key));
            GUI.color = Color.white;
            Widgets.Label(r.RightPart(0.78f), what);
        }

        // ---------------------------------------------------------------- tabs

        // Draws the chosen tab's left column (l set) or right column (r set).
        private static void Tab(Listing_Standard l, Listing_Standard r, IsoRimSettings st)
        {
            switch (tab)
            {
                case 0:
                    ViewTab(l, r, st);
                    break;
                case 1:
                    ColourTab(l, r, st);
                    break;
                case 2:
                    WorldTab(l, r, st);
                    break;
                case 4:
                    SeeThroughTab(l, r, st);
                    break;
                default:
                    ObjectsTab(l, r, st);
                    break;
            }
        }

        private static void ViewTab(Listing_Standard l, Listing_Standard r, IsoRimSettings st)
        {
            if (l != null)
            {
                Section(l, "Camera", "How the map is seen while the 3D view is on.");
                Check(l, "Isometric view", ref st.isometric, "The camera turned 45 degrees and lowered, as in isometric games. Off: north is up.");
                Check(l, "Turn in 45° steps", ref st.snap45, "Q and E turn the camera an eighth of a turn at a time. Off: a quarter turn. Either way the camera swings smoothly.");
                if (st.isometric)
                {
                    st.isoPitch = Slider(l, "Isometric camera angle", st.isoPitch, View3D.MinPitch, View3D.MaxPitch, st.isoPitch.ToString("0") + "°",
                        "35 is the true isometric angle.");
                }
                else
                {
                    st.pitch = Slider(l, "Camera angle", st.pitch, View3D.MinPitch, View3D.MaxPitch, st.pitch.ToString("0") + "°", "90 looks straight down.");
                }
                st.wallHeight = Slider(l, "Wall height", st.wallHeight, 0.5f, 4f, st.wallHeight.ToString("0.0") + " cells");

            }
            if (r != null)
            {
                Section(r, "Keys", "Change them under Options > Keyboard configuration > IsoRim.");
                KeyRow(r, R3DKeyDefOf.R3D_ToggleView, "3D view on and off");
                KeyRow(r, R3DKeyDefOf.R3D_Isometric, "isometric or straight-on");
                KeyRow(r, R3DKeyDefOf.R3D_TurnLeft, "turn the camera left");
                KeyRow(r, R3DKeyDefOf.R3D_TurnRight, "turn the camera right");
                KeyRow(r, R3DKeyDefOf.R3D_TiltDown, "lower the camera");
                KeyRow(r, R3DKeyDefOf.R3D_TiltUp, "raise the camera");
                KeyRow(r, R3DKeyDefOf.R3D_ToggleRoofs, "roofs on and off");
                Note(r, "The 3D view and the roofs also have buttons in the bottom right corner of the screen, next to the game's own.");

                Section(r, "Advanced");
                st.feetOffset = Slider(r, "Where upright sprites stand", st.feetOffset, 0f, 0.5f, st.feetOffset.ToString("0.00"),
                    "Only for people and animals still drawn as flat sprites.");
                st.squash = Slider(r, "Layer flattening", st.squash, 0.002f, 0.004f, st.squash.ToString("0.0000"),
                    "How tightly the game's flat drawing layers are pressed together. Leave it unless things flicker.");
            }
        }

        private static void SeeThroughTab(Listing_Standard l, Listing_Standard r, IsoRimSettings st)
        {
            if (l != null)
            {
                Section(l, "Walls", "Walls are lowered so you can see and click what is behind them. Natural rock never is.");
                Check(l, "Lower walls near the pointer", ref st.cutHover);
                if (st.cutHover)
                {
                    st.dissolveRadius = Slider(l, "Reach round the pointer", st.dissolveRadius, 1.5f, 8f, st.dissolveRadius.ToString("0.0") + " cells");
                    Check(l, "Only walls in front of the pointer", ref st.cutFrontOnly, "Only the walls between the camera and the pointer are lowered; the ones behind it stay up.");
                }
                Check(l, "Lower walls near colonists", ref st.cutNearColonists, "Walls between the camera and each colonist are lowered wherever they go. Costs a little more as they move about.");
                if (st.cutNearColonists)
                {
                    st.colonistRadius = Slider(l, "Reach round each colonist", st.colonistRadius, 1f, 5f, st.colonistRadius.ToString("0.0") + " cells");
                }
                Check(l, "Lower walls in front of every room", ref st.cutRooms, "Walls between the camera and a roofed room are always drawn lowered.");
                Check(l, "  ...and rock in front of rooms dug into mountains", ref st.cutRock, "Up to three cells of rock between the camera and a room are lowered; the rest of the mountain stays whole.");
                st.cutHeight = Slider(l, "Height left of a lowered wall", st.cutHeight, 0.05f, 0.9f, (st.cutHeight * 100f).ToString("0") + "%");
            }
            if (r != null)
            {
                Section(r, "Trees", "Trees drop their leaves while something you want to see is under them.");
                Check(r, "Thin out trees near the pointer", ref st.treesNearPointer);
                Check(r, "Thin out trees near colonists", ref st.treesNearColonists);
                if (st.treesNearPointer || st.treesNearColonists)
                {
                    st.treeRadius = Slider(r, "Reach", st.treeRadius, 1f, 6f, st.treeRadius.ToString("0.0") + " cells");
                }

                Section(r, "Roofs", "Only while roofs are shown.");
                Check(r, "Lift the roof of the room under the pointer", ref st.roofHover);
                Check(r, "Lift the roofs of rooms with colonists in them", ref st.roofOverColonists);
            }
        }

        private static void ColourTab(Listing_Standard l, Listing_Standard r, IsoRimSettings st)
        {
            if (l != null)
            {
                Section(l, "Colour look", "A colour grade over the 3D view. The interface is not affected.");
                Check(l, "Colour grade on", ref st.grade);
                if (st.grade)
                {
                    LookPreset look = Looks.Find(st.lookName);
                    Rect b = l.GetRect(30f);
                    if (Widgets.ButtonText(b, "Look: " + look.label))
                    {
                        List<FloatMenuOption> options = new List<FloatMenuOption>();
                        foreach (LookPreset p in Looks.Presets)
                        {
                            LookPreset chosen = p;
                            options.Add(new FloatMenuOption(p.label, delegate
                            {
                                st.lookName = chosen.name;
                                st.lutFile = "";
                            }));
                        }
                        Find.WindowStack.Add(new FloatMenu(options));
                    }
                    Note(l, look.description);
                    Preview(l, Looks.Current());

                    if (look.name == Looks.CustomName)
                    {
                        st.saturation = Slider(l, "Colour kept", st.saturation, 0.5f, 1f, (st.saturation * 100f).ToString("0") + "%");
                        st.brightness = Slider(l, "Brightness", st.brightness, 0.6f, 1f, (st.brightness * 100f).ToString("0") + "%");
                    }
                    else
                    {
                        st.lookStrength = Slider(l, "Strength", st.lookStrength, 0f, 1f, (st.lookStrength * 100f).ToString("0") + "%");
                    }

                    Section(l, "Exact grading (LUT)");
                    if (Lut.Available)
                    {
                        Check(l, "Use lookup tables", ref st.useLut, "Each look comes as a lookup table too, which grades the picture exactly. Off: the always-available blend is used.");
                        if (st.useLut)
                        {
                            Rect fb = l.GetRect(28f);
                            string shown = st.lutFile.NullOrEmpty() ? "the look's own table" : st.lutFile;
                            if (Widgets.ButtonText(fb, "Table: " + shown))
                            {
                                List<FloatMenuOption> options = new List<FloatMenuOption>();
                                options.Add(new FloatMenuOption("the look's own table", delegate { st.lutFile = ""; }));
                                foreach (string f in Lut.Files)
                                {
                                    string chosen = f;
                                    options.Add(new FloatMenuOption(f, delegate { st.lutFile = chosen; }));
                                }
                                Find.WindowStack.Add(new FloatMenu(options));
                            }
                            Note(l, "Put your own 1024 x 32 LUT strips (.png) in the mod's LUTs folder. The preview above shows the blended version.");
                        }
                    }
                    else
                    {
                        Note(l, "Not installed. The looks above work without it. For exact LUT grading, build the small shader bundle as the README describes and put it in the mod's Shaders folder.");
                    }
                }
            }
            if (r != null)
            {
                Section(r, "Shadows");
                Check(r, "Soft shadows under everything", ref st.groundShadows);
                Check(r, "Trees cast sun shadows", ref st.treeShadows);
                if (st.treeShadows)
                {
                    st.treeShadowLength = Slider(r, "Tree shadow length", st.treeShadowLength, 0.05f, 0.5f, st.treeShadowLength.ToString("0.00"));
                }

                Section(r, "Light");
                Check(r, "Night and indoor darkness on raised things", ref st.lightingFix);
                Check(r, "Unexplored areas are a solid lid", ref st.fogLid);
                Check(r, "Sun moves through the day", ref st.sunMoves, "The sun rises in the east, stands in the south at noon and sets in the west, and its light on walls, roofs and furniture moves on a few times a day. Off: it stays at its mid-morning place. Turning the camera never changes the light.");
            }
        }

        private static void WorldTab(Listing_Standard l, Listing_Standard r, IsoRimSettings st)
        {
            if (l != null)
            {
                Section(l, "Ground", "Only the picture changes, and only while the 3D view is on.");
                Check(l, "Natural ground in the mod's style", ref st.groundStyle);
                if (st.groundStyle)
                {
                    Check(l, "Soil drawn as soft grass", ref st.grassSoil, "Rich soil gets a darker, lusher grass so farmland still stands out.");
                }
                Check(l, "Built floors in the mod's style", ref st.floorStyle);

                Section(l, "Water");
                Check(l, "Stylised water", ref st.waterStyle, "Faceted bands of colour from the shore to the deep, foam along the shores, streaks on rivers and sparkles.");
            }
            if (r != null)
            {
                Section(r, "Roofs", "Built roofs as slate lids over your rooms, and rock roofs over caves.");
                bool roofs = st.showRoofs;
                Check(r, "Show roofs", ref roofs, "All roofs or none: switch them off again to see inside.");
                if (roofs != st.showRoofs)
                {
                    Roofs.Set(roofs);
                }
                Rect rb = r.GetRect(28f);
                if (Widgets.ButtonText(rb, "Roof colour: " + SectionLayer_IsoRimRoofs.StyleNames[Mathf.Clamp(st.roofStyle, 0, 3)]))
                {
                    List<FloatMenuOption> options = new List<FloatMenuOption>();
                    for (int i = 0; i < SectionLayer_IsoRimRoofs.StyleNames.Length; i++)
                    {
                        int chosen = i;
                        options.Add(new FloatMenuOption(SectionLayer_IsoRimRoofs.StyleNames[i], delegate
                        {
                            st.roofStyle = chosen;
                            Roofs.Rebuild();
                        }));
                    }
                    Find.WindowStack.Add(new FloatMenu(options));
                }
                Note(r, "Built roofs rise from every edge to a ridge, like hipped roofs. There is a button for them in the bottom right corner of the screen, and a key you can set.");
            }
        }

        private static void ObjectsTab(Listing_Standard l, Listing_Standard r, IsoRimSettings st)
        {
            if (l != null)
            {
                Section(l, "Buildings and nature", "Switch one off if it misbehaves.");
                Check(l, "Walls and rock as solid blocks", ref st.walls3D);
                Check(l, "Walls use the mod's textures", ref st.texturedWalls);
                Check(l, "Rock has broken, sloping edges", ref st.ruggedRock);
                Check(l, "Doors", ref st.doors3D);
                Check(l, "Hand-made models", ref st.models3D, "Furniture, machines, wrecks, people, animals and armour.");
                Check(l, "Trees", ref st.trees3D);
                Check(l, "Grass, flowers and crops", ref st.smallPlants3D, "Thousands of these on a big map cost memory; switch off if it drags.");
                Check(l, "Everything else, from its sprite", ref st.autoExtrude);
                Check(l, "Items get a little thickness", ref st.thickItems);
                if (st.thickItems)
                {
                    st.itemThickness = Slider(l, "  How thick items are", st.itemThickness, 0f, 1f,
                        st.itemThickness <= 0.02f ? "flat" : (st.itemThickness * 100f).ToString("0") + "%",
                        "Thins out items, weapons and clothes on the ground. All the way down lays them flat.");
                }
                Check(l, "Items and weapons use the game's art", ref st.itemsFromArt,
                    "Items, weapons and clothing are made solid from their own game sprites, so they look exactly like RimWorld. Off: the mod's hand-made item models.");
                Check(l, "Other plants stand upright", ref st.uprightPlants);
                Check(l, "Map edge cut through the earth", ref st.mapEdge3D, "The edge of the map shows layers of soil and rock, like a diorama.");
            }
            if (r != null)
            {
                Section(r, "Creatures and effects");
                Check(r, "Colonists and other people", ref st.pawns3D);
                Check(r, "Animals", ref st.animals3D);
                Check(r, "Weapons in hand", ref st.heldWeapons3D);
                Check(r, "Work animations with tools", ref st.workAnimations, "Axes, pickaxes, hammers, scythes, hoes and brooms while colonists work.");
                Check(r, "Blueprints show the finished build", ref st.ghosts3D, "Blueprints, frames and the placement preview as see-through 3D models.");
                Check(r, "Damage marks on buildings", ref st.damage3D);
                Check(r, "Flames, smoke, steam and sparkles", ref st.effects3D);
                Check(r, "Sprites stand upright", ref st.uprightPawns, "For people and animals without a model.");

                Section(r, "Model style");
                Check(r, "Textures on models", ref st.texturedModels);
                Check(r, "Dark outlines on models", ref st.outlines);
            }
        }

        // Two rows of colour chips: as they are, and under the look.
        private static void Preview(Listing_Standard l, LookPreset look)
        {
            Rect r = l.GetRect(34f);
            float w = r.width / Palette.Length;
            for (int i = 0; i < Palette.Length; i++)
            {
                Rect top = new Rect(r.x + i * w, r.y, w - 2f, 15f);
                Rect bottom = new Rect(r.x + i * w, r.y + 17f, w - 2f, 15f);
                Widgets.DrawBoxSolid(top, Palette[i]);
                Widgets.DrawBoxSolid(bottom, Looks.Apply(look, Palette[i]));
            }
            TooltipHandler.TipRegion(r, "Top: colours as they are. Bottom: under this look.");
            l.Gap(2f);
        }
    }

    [DefOf]
    public static class R3DKeyDefOf
    {
        public static KeyBindingDef R3D_ToggleView;
        public static KeyBindingDef R3D_Isometric;
        public static KeyBindingDef R3D_TurnLeft;
        public static KeyBindingDef R3D_TurnRight;
        public static KeyBindingDef R3D_TiltUp;
        public static KeyBindingDef R3D_TiltDown;
        public static KeyBindingDef R3D_ToggleRoofs;

        static R3DKeyDefOf()
        {
            DefOfHelper.EnsureInitializedInCtor(typeof(R3DKeyDefOf));
        }
    }

    // The mod's buttons for the bottom right corner. Loaded on the main thread at startup.
    [StaticConstructorOnStartup]
    public static class R3DIcons
    {
        public static readonly Texture2D View3D = ContentFinder<Texture2D>.Get("IsoRim/UI/View3D", false) ?? BaseContent.BadTex;
        public static readonly Texture2D Roofs = ContentFinder<Texture2D>.Get("IsoRim/UI/Roofs", false) ?? BaseContent.BadTex;
    }

    // Runs once on the main thread after all defs are loaded.
    [StaticConstructorOnStartup]
    public static class IsoRimStartup
    {
        static IsoRimStartup()
        {
            ModLog.Debug("[IsoRim] Code loaded.");

            try
            {
                Patches.ApplyAll();
            }
            catch (Exception e)
            {
                Log.Error("[IsoRim] Could not apply patches: " + e);
            }

            try
            {
                ModelLibrary.LoadAll();
            }
            catch (Exception e)
            {
                Log.Error("[IsoRim] Could not load models: " + e);
            }
        }
    }
}
