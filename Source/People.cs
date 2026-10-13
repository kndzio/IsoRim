using System;
using System.Collections.Generic;
using System.IO;
using RimWorld;
using UnityEngine;
using Verse;

namespace IsoRim
{
    // People drawn as 3D figures in place of their sprites.
    //
    // A figure keeps the game's own proportions (a big round head on a simple body with no arms
    // or legs) and is put together from plain parts, each coloured from the person it shows:
    //   - the body, in the game's five builds (and smaller for children);
    //   - skin colour; hair in the person's own colour and roughly their own cut; a beard;
    //   - what they are wearing: trousers and shirt colour the lower and upper body, a jacket or
    //     a long coat goes over them, armour adds plates, and a hat, helmet or hood goes on top.
    // Because all of it is read from the person, anyone the game makes up gets a figure to match.
    // Like the animals, a figure turns to face the way it is really walking.
    public static class People
    {
        // What one person looks like. Worked out from the pawn now and then, not every frame.
        private class Look
        {
            public int frame;
            public float size = 1f;
            public float headWide = 1f;
            public float shoulders = 1f;
            public Model lower;
            public Model upper;
            public Model coat;
            public Model hair;
            public Model beard;
            public Model hat;
            public Model legArmour;
            public bool pads;
            public bool visor;
            public bool faceHidden;
            public Color skin = Color.white;
            public Color hairColor = Color.white;
            public Color upperColor = Color.white;
            public Color lowerColor = Color.white;
            public Color coatColor = Color.white;
            public Color hatColor = Color.white;
            public Color legArmourColor = Color.white;

            // Ready-made meshes of this look, by facing, body or head, and alive or dead.
            public readonly Dictionary<int, List<DynamicModels.Part>> meshes = new Dictionary<int, List<DynamicModels.Part>>();
            public int builtForLight = -1;

            public bool SameAs(Look o)
            {
                return o != null && size == o.size && headWide == o.headWide && shoulders == o.shoulders && lower == o.lower && upper == o.upper
                    && coat == o.coat && hair == o.hair && beard == o.beard && hat == o.hat && pads == o.pads && visor == o.visor
                    && legArmour == o.legArmour && legArmourColor == o.legArmourColor && faceHidden == o.faceHidden
                    && skin == o.skin && hairColor == o.hairColor && upperColor == o.upperColor && lowerColor == o.lowerColor
                    && coatColor == o.coatColor && hatColor == o.hatColor;
            }

            public void Forget()
            {
                foreach (List<DynamicModels.Part> parts in meshes.Values)
                {
                    DynamicModels.Destroy(parts);
                }
                meshes.Clear();
            }
        }

        private static readonly List<Model> mergeModels = new List<Model>();
        private static readonly List<Matrix4x4> mergeLocals = new List<Matrix4x4>();
        private static readonly List<Color> mergeTints = new List<Color>();

        // The body (head = false) or the head of a figure as ready-made meshes.
        private static List<DynamicModels.Part> Merged(Look look, bool headPart, bool dead, int turned)
        {
            if (look.builtForLight != R3DMaterials.LightStep)
            {
                look.Forget();
                look.builtForLight = R3DMaterials.LightStep;
            }
            int key = turned * 4 + (headPart ? 2 : 0) + (dead ? 1 : 0);
            List<DynamicModels.Part> parts;
            if (look.meshes.TryGetValue(key, out parts))
            {
                return parts;
            }
            mergeModels.Clear();
            mergeLocals.Clear();
            mergeTints.Clear();
            if (headPart)
            {
                Matrix4x4 headPlace = Matrix4x4.Scale(new Vector3(look.headWide, 1f, 1f));
                Color skin = dead ? Color.Lerp(look.skin, new Color(0.55f, 0.58f, 0.52f), 0.35f) : look.skin;
                AddPart(head, headPlace, skin);
                if (!look.visor && !look.faceHidden)
                {
                    AddPart(face, headPlace, Color.white);
                }
                AddPart(look.hair, headPlace, look.hairColor);
                AddPart(look.beard, headPlace, look.hairColor);
                AddPart(look.hat, headPlace, look.hatColor);
                if (look.hat != null && look.visor)
                {
                    AddPart(visor, headPlace, Color.white);
                }
            }
            else
            {
                AddPart(look.lower, Matrix4x4.identity, look.lowerColor);
                AddPart(look.upper, Matrix4x4.identity, look.upperColor);
                AddPart(look.legArmour, Matrix4x4.identity, look.legArmourColor);
                AddPart(look.coat, Matrix4x4.identity, look.coatColor);
                if (look.pads)
                {
                    AddPart(pads, Matrix4x4.Scale(new Vector3(look.shoulders, 1f, 1.05f)), look.coat != null ? look.coatColor : look.upperColor);
                }
            }
            parts = DynamicModels.BuildMerged(mergeModels, mergeLocals, mergeTints, turned);
            look.meshes[key] = parts;
            return parts;
        }

        private static void AddPart(Model m, Matrix4x4 local, Color tint)
        {
            if (m == null)
            {
                return;
            }
            mergeModels.Add(m);
            mergeLocals.Add(local);
            mergeTints.Add(tint);
        }

        private const int RefreshFrames = 90;
        private const float HeadHeight = 0.98f;   // where the middle of the head is on the figure

        private static readonly Dictionary<int, Look> looks = new Dictionary<int, Look>();
        private static readonly Dictionary<string, Model> models = new Dictionary<string, Model>();
        private static Model head;
        private static Model face;
        private static Model visor;
        private static Model pads;
        private static bool tried;

        // Draws the person at drawLoc. Returns false if they cannot be drawn as a figure, in
        // which case the game's sprite must be drawn as usual. handHeight is how high above the
        // ground a weapon is held and facing which way the figure faces, for whoever draws the weapon.
        public static bool Draw(Pawn pawn, Vector3 drawLoc, out float handHeight, out float facing, out bool standing)
        {
            handHeight = 0.5f;
            facing = 0f;
            standing = false;
            if (pawn.story == null || pawn.def == null || pawn.def.defName != "Human" || Hidden(pawn))
            {
                return false;
            }
            if (!tried)
            {
                tried = true;
                head = Part("person_head");
                face = Part("person_face");
                visor = Part("person_visor");
                pads = Part("person_pads");
            }
            if (head == null)
            {
                return false;
            }
            Look look = LookOf(pawn);
            if (look == null || look.upper == null || look.lower == null)
            {
                return false;
            }

            bool dead = pawn.Dead;
            bool lying = dead || pawn.GetPosture() != PawnPosture.Standing;
            float size = look.size;
            float yaw;
            float phase = 0f;
            float gait = 0f;
            if (dead)
            {
                yaw = pawn.Rotation.AsAngle + (Hashing.Unit(pawn.thingIDNumber, 3, 9) - 0.5f) * 60f;
            }
            else
            {
                Animals.Track(pawn, drawLoc, lying, 0.9f * size, out yaw, out phase, out gait);
            }

            float ground = 0f;
            bool headOnly = false;
            Matrix4x4 pose;
            Model workTool = null;
            Matrix4x4 workLocal = Matrix4x4.identity;
            float workLean = 0f;
            float workDip = 0f;
            if (lying)
            {
                // On their back, head toward the south of the figure's own space before it is turned.
                Quaternion onBack = Quaternion.AngleAxis(-90f, Vector3.right);
                Building_Bed bed = dead ? null : pawn.CurrentBed();
                if (bed != null)
                {
                    // In a bed the person's place is where their head is, and they lie along the bed.
                    yaw = bed.Rotation.AsAngle;
                    ground = Forms.HeightOf(bed);
                    headOnly = ground > 0.05f && bed.def.building != null && !bed.def.building.bed_showSleeperBody;
                    pose = Matrix4x4.Translate(new Vector3(0f, (headOnly ? 0.24f : 0.15f) * size, HeadHeight * size)) * Matrix4x4.Rotate(onBack);
                }
                else
                {
                    pose = Matrix4x4.Translate(new Vector3(0f, 0.15f * size, 0.55f * size)) * Matrix4x4.Rotate(onBack);
                    if (!dead && pawn.pather != null && pawn.pather.Moving)
                    {
                        yaw += 180f;   // crawling: head first, the way they are going
                    }
                }
            }
            else
            {
                // A little waddle and bounce in step.
                float bob = Mathf.Abs(Mathf.Sin(phase)) * 0.035f * size * gait;
                float sway = Mathf.Sin(phase) * 4.5f * gait;
                pose = Matrix4x4.Translate(new Vector3(0f, bob, 0f)) * Matrix4x4.Rotate(Quaternion.AngleAxis(sway, Vector3.forward));
                standing = true;

                // At work: face the work, lean into each stroke and swing the tool.
                if (IsoRimMod.Settings.workAnimations && WorkAnimations.Animate(pawn, drawLoc, ref yaw, out workTool, out workLocal, out workLean, out workDip))
                {
                    pose = Matrix4x4.Translate(new Vector3(0f, -workDip * size, 0f)) * Matrix4x4.Rotate(Quaternion.AngleAxis(workLean, Vector3.right));
                }
            }

            Vector3 at = new Vector3(drawLoc.x, ground, drawLoc.z);
            Matrix4x4 whole = pose * Matrix4x4.Scale(new Vector3(size, size, size));

            // The whole figure is two ready-made meshes (body and head), each a single draw, put
            // together once for this look and the way it is facing.
            int turned = Mathf.RoundToInt(Mathf.Repeat(yaw, 360f) / 45f) % 8;
            if (!headOnly)
            {
                DynamicModels.DrawParts(Merged(look, false, dead, turned), at, yaw, whole);
            }
            DynamicModels.DrawParts(Merged(look, true, dead, turned), at, yaw, whole);
            if (workTool != null)
            {
                // The tool is placed in the figure's own space, so it leans and dips with it.
                DynamicModels.DrawLocal(workTool, at, yaw, whole * workLocal, Color.white, "Wood");
            }

            if (ground <= 0f)
            {
                GroundShadows.Blob(at, yaw, (lying ? 0.30f : 0.34f) * size, (lying ? 0.70f : 0.30f) * size);
            }
            handHeight = 0.46f * size;
            facing = yaw;
            return true;
        }

        // People who are invisible must stay so: they keep their sprite, which the game hides.
        public static bool Hidden(Pawn pawn)
        {
            if (pawn.health == null || pawn.health.hediffSet == null)
            {
                return false;
            }
            List<Hediff> all = pawn.health.hediffSet.hediffs;
            for (int i = 0; i < all.Count; i++)
            {
                if (all[i].def != null && all[i].def.defName != null && all[i].def.defName.IndexOf("Invisib", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    return true;
                }
            }
            return false;
        }

        internal static Model Part(string name)
        {
            Model m;
            if (models.TryGetValue(name, out m))
            {
                return m;
            }
            m = IsoRimMod.RootDir != null ? ModelLibrary.LoadFile(Path.Combine(IsoRimMod.RootDir, "Models", name + ".obj")) : null;
            models[name] = m;
            return m;
        }

        private static Look LookOf(Pawn pawn)
        {
            Look look;
            int frame = Time.frameCount;
            if (looks.TryGetValue(pawn.thingIDNumber, out look) && frame - look.frame < RefreshFrames)
            {
                return look;
            }
            Look old = look;
            if (looks.Count > 600)
            {
                foreach (Look l in looks.Values)
                {
                    l.Forget();
                }
                looks.Clear();   // people long gone; the ones still about are worked out again
                old = null;
            }
            try
            {
                look = Work(pawn);
                if (old != null)
                {
                    if (look != null && old.SameAs(look))
                    {
                        look = old;   // nothing has changed: keep the meshes already made
                    }
                    else
                    {
                        old.Forget();
                    }
                }
            }
            catch (Exception e)
            {
                look = null;
                Log.ErrorOnce("[IsoRim] Working out what a person looks like failed: " + e, 93611090);
            }
            if (look != null)
            {
                // Spread the refreshes out so a crowd is not all worked out on the same frame.
                look.frame = frame - (pawn.thingIDNumber & 31);
                looks[pawn.thingIDNumber] = look;
            }
            return look;
        }

        private static bool Has(string text, string word)
        {
            return text.IndexOf(word, StringComparison.OrdinalIgnoreCase) >= 0;
        }

        private static Look Work(Pawn pawn)
        {
            Look look = new Look();
            Pawn_StoryTracker story = pawn.story;

            // Build.
            string bodyName = story.bodyType != null ? (story.bodyType.defName ?? "") : "";
            string build = "male";
            if (Has(bodyName, "Female"))
            {
                build = "female";
            }
            else if (Has(bodyName, "Thin") || Has(bodyName, "Child"))
            {
                build = "thin";
            }
            else if (Has(bodyName, "Hulk"))
            {
                build = "hulk";
            }
            else if (Has(bodyName, "Fat") || Has(bodyName, "Baby"))
            {
                build = "fat";
            }
            look.shoulders = build == "hulk" ? 1.36f : (build == "male" || build == "fat" ? 1f : 0.84f);
            float grown = 1f;
            if (pawn.ageTracker != null && pawn.ageTracker.CurLifeStage != null)
            {
                grown = pawn.ageTracker.CurLifeStage.bodySizeFactor;
            }
            look.size = Mathf.Lerp(0.5f, 1f, Mathf.Clamp01(grown));
            look.lower = Part("person_" + build + "_lower");
            look.upper = Part("person_" + build + "_upper");

            // Head, hair and beard.
            string headName = story.headType != null ? (story.headType.defName ?? "") : "";
            look.headWide = Has(headName, "Narrow") ? 0.9f : (Has(headName, "Wide") ? 1.07f : 1f);
            look.skin = story.SkinColor;
            look.hairColor = story.HairColor;
            string hairKind = HairKind(story.hairDef != null ? (story.hairDef.defName ?? "") : "");
            string beardKind = null;
            if (pawn.style != null && pawn.style.beardDef != null)
            {
                string beardName = pawn.style.beardDef.defName ?? "";
                if (!Has(beardName, "NoBeard") && !Has(beardName, "Stubble") && !Has(beardName, "Moustache") && !Has(beardName, "Mustache"))
                {
                    beardKind = Has(beardName, "Goatee") || Has(beardName, "Soul") || Has(beardName, "Chin") ? "goatee" : "full";
                }
            }

            // Clothes. Each layer over the body gives its colour to the part it covers; the
            // outermost one wins. A shell layer becomes a coat worn over the rest.
            look.upperColor = look.skin;
            look.lowerColor = look.skin;
            int upperLayer = -1;
            int lowerLayer = -1;
            string hatKind = null;
            string coatKind = null;
            string legArmourKind = null;
            string vestKind = null;
            string shellArmourKind = null;
            Color vestColour = Color.white;
            Color shellArmourColour = Color.white;
            if (pawn.apparel != null)
            {
                List<Apparel> worn = pawn.apparel.WornApparel;
                for (int i = 0; i < worn.Count; i++)
                {
                    Apparel a = worn[i];
                    ApparelProperties props = a.def != null ? a.def.apparel : null;
                    if (props == null)
                    {
                        continue;
                    }
                    string name = a.def.defName ?? "";
                    Color colour = ApparelColour(a);
                    bool torso = Covers(props, "Torso");
                    bool legs = Covers(props, "Legs");
                    bool onHead = Covers(props, "FullHead") || Covers(props, "UpperHead");
                    bool armour = Has(name, "Armor") || Has(name, "Armour") || Has(name, "Flak") || Has(name, "Plate") || Has(name, "Cataphract")
                        || Has(name, "Marine") || Has(name, "Recon") || Has(name, "Phoenix") || Has(name, "Prestige");

                    string armourKind = onHead && !torso && !legs ? null : ArmourKind(name);
                    if (armourKind == "flakpants")
                    {
                        legArmourKind = armourKind;
                        look.legArmourColor = colour;
                        continue;
                    }
                    if (armourKind == "flakvest")
                    {
                        vestColour = colour;
                        vestKind = armourKind;
                        continue;
                    }
                    if (armourKind != null && torso)
                    {
                        shellArmourKind = armourKind;
                        shellArmourColour = colour;
                        if (legs && (armourKind == "marine" || armourKind == "cataphract" || armourKind == "recon"))
                        {
                            look.lowerColor = colour;
                            lowerLayer = 3;
                        }
                        continue;
                    }

                    if (onHead && !torso && !legs)
                    {
                        if (OnLayer(props, "Overhead") || hatKind == null)
                        {
                            hatKind = HatKind(name, Covers(props, "FullHead"));
                            look.hatColor = colour;
                        }
                        continue;
                    }

                    int layer = OnLayer(props, "Shell") ? 2 : (OnLayer(props, "Middle") ? 1 : (OnLayer(props, "OnSkin") ? 0 : -1));
                    if (layer < 0)
                    {
                        continue;   // belts and the like
                    }
                    if (layer == 2 && torso)
                    {
                        bool longCoat = legs || Has(name, "Duster") || Has(name, "Parka") || Has(name, "Robe") || Has(name, "Cape") || Has(name, "Coat");
                        coatKind = longCoat && !armour ? "coat_long" : "coat_short";
                        look.coatColor = colour;
                        look.pads |= armour;
                        if (armour && legs && layer > lowerLayer)
                        {
                            look.lowerColor = colour;   // armour that reaches the legs
                            lowerLayer = layer;
                        }
                        continue;
                    }
                    if (torso && layer > upperLayer)
                    {
                        look.upperColor = colour;
                        upperLayer = layer;
                        look.pads |= armour;
                    }
                    if (legs && layer > lowerLayer)
                    {
                        look.lowerColor = colour;
                        lowerLayer = layer;
                    }
                }
            }
            // Armour the mod has a shape for takes the place of a coat (it is worn on the same
            // outer layer); a flak vest shows only when nothing is worn over it.
            if (shellArmourKind != null)
            {
                look.coat = Part("person_" + build + "_armor_" + shellArmourKind);
                look.coatColor = shellArmourColour;
                look.pads = false;
            }
            else if (coatKind != null)
            {
                look.coat = Part("person_" + build + "_" + coatKind);
            }
            else if (vestKind != null)
            {
                look.coat = Part("person_" + build + "_armor_" + vestKind);
                look.coatColor = vestColour;
                look.pads = false;
            }
            if (legArmourKind != null)
            {
                look.legArmour = Part("person_" + build + "_armor_" + legArmourKind);
            }

            if (hatKind != null)
            {
                look.hat = Part("person_hat_" + hatKind);
                look.visor = hatKind == "fullhelm";
                look.faceHidden = SealedHelmet(hatKind) || hatKind == "combat";
            }
            // Hair shows unless a helmet or hood covers the whole head; under a hat only hair that
            // hangs below it shows.
            bool covered = hatKind == "helmet" || hatKind == "hood" || hatKind == "combat" || SealedHelmet(hatKind);
            bool hangs = hairKind == "long" || hairKind == "medium" || hairKind == "ponytail" || hairKind == "short";
            if (hairKind != null && !covered && (hatKind == null || hangs))
            {
                look.hair = Part("person_hair_" + hairKind);
            }
            if (beardKind != null && !SealedHelmet(hatKind))
            {
                look.beard = Part("person_beard_" + beardKind);
            }
            return look;
        }

        private static bool Covers(ApparelProperties props, string group)
        {
            if (props.bodyPartGroups == null)
            {
                return false;
            }
            for (int i = 0; i < props.bodyPartGroups.Count; i++)
            {
                if (props.bodyPartGroups[i] != null && props.bodyPartGroups[i].defName == group)
                {
                    return true;
                }
            }
            return false;
        }

        private static bool OnLayer(ApparelProperties props, string layer)
        {
            if (props.layers == null)
            {
                return false;
            }
            for (int i = 0; i < props.layers.Count; i++)
            {
                if (props.layers[i] != null && props.layers[i].defName == layer)
                {
                    return true;
                }
            }
            return false;
        }

        // Which of the mod's hair shapes is nearest to one of the game's many hair styles, going
        // by its name. Null means no hair.
        private static string HairKind(string name)
        {
            if (name.Length == 0 || Has(name, "Bald") || Has(name, "Shaved"))
            {
                return null;
            }
            if (Has(name, "Mohawk") || Has(name, "Fauxhawk") || Has(name, "Warhawk") || Has(name, "Fin"))
            {
                return "mohawk";
            }
            if (Has(name, "Afro") || Has(name, "Curly") || Has(name, "Poof") || Has(name, "Fro"))
            {
                return "afro";
            }
            if (Has(name, "Pony") || Has(name, "Tail") || Has(name, "Braid") || Has(name, "Queue"))
            {
                return "ponytail";
            }
            if (Has(name, "Bun") || Has(name, "Topknot") || Has(name, "Knot") || Has(name, "Dango"))
            {
                return "bun";
            }
            if (Has(name, "Spik") || Has(name, "Mess") || Has(name, "Wild") || Has(name, "Scat") || Has(name, "Rebel") || Has(name, "Flowy"))
            {
                return "spiky";
            }
            if (Has(name, "Long") || Has(name, "Princess") || Has(name, "Wavy") || Has(name, "Lace") || Has(name, "Mane") || Has(name, "Elder")
                || Has(name, "Senorita") || Has(name, "Curtain"))
            {
                return "long";
            }
            if (Has(name, "Bob") || Has(name, "Mop") || Has(name, "Shoulder") || Has(name, "Pigtails") || Has(name, "Decent") || Has(name, "Greasy")
                || Has(name, "Bowl") || Has(name, "Lackland") || Has(name, "Tuft"))
            {
                return "medium";
            }
            return "short";
        }

        private static bool SealedHelmet(string hatKind)
        {
            return hatKind == "fullhelm" || hatKind == "marine_helm" || hatKind == "cataphract_helm" || hatKind == "recon_helm";
        }

        // Armour the mod has a worn shape for, by the game's names for it (and the names the
        // DLCs and most mods use for theirs). Null for anything else.
        private static string ArmourKind(string name)
        {
            if (Has(name, "Cataphract"))
            {
                return "cataphract";
            }
            if (Has(name, "PowerArmor") || Has(name, "Marine") || Has(name, "PowerArmour"))
            {
                return "marine";
            }
            if (Has(name, "Recon"))
            {
                return "recon";
            }
            if (Has(name, "PlateArmor") || Has(name, "PlateArmour"))
            {
                return "plate";
            }
            if (Has(name, "FlakJacket"))
            {
                return "flakjacket";
            }
            if (Has(name, "FlakVest"))
            {
                return "flakvest";
            }
            if (Has(name, "FlakPants"))
            {
                return "flakpants";
            }
            return null;
        }

        // The colour of a piece of clothing as the game shows it. Things made from cloth or
        // leather are drawn in that material's colour; things that are not (power armour, flak)
        // have their colours painted into the sprite, so its average colour is used instead.
        private static Color ApparelColour(Apparel a)
        {
            Color c = a.DrawColor;
            if (a.def.MadeFromStuff)
            {
                return c;
            }
            CompColorable colorable = a.TryGetComp<CompColorable>();
            if (colorable != null && colorable.Active)
            {
                return c;
            }
            return SpriteColors.MeanFor(a);
        }

        private static string HatKind(string name, bool fullHead)
        {
            if (Has(name, "Helmet") || Has(name, "Helm"))
            {
                if (Has(name, "Cataphract"))
                {
                    return "cataphract_helm";
                }
                if (Has(name, "PowerArmor") || Has(name, "Marine"))
                {
                    return "marine_helm";
                }
                if (Has(name, "Recon"))
                {
                    return "recon_helm";
                }
                if (Has(name, "Advanced"))
                {
                    return "combat";
                }
                bool sealedHelmet = fullHead && (Has(name, "Power") || Has(name, "Recon") || Has(name, "Marine") || Has(name, "Cataphract")
                    || Has(name, "Armor") || Has(name, "Phoenix") || Has(name, "Gunlink") || Has(name, "Prestige"));
                return sealedHelmet ? "fullhelm" : "helmet";
            }
            if (Has(name, "Cowboy") || Has(name, "Shadecone") || Has(name, "Brim") || Has(name, "Sun"))
            {
                return "brim";
            }
            if (Has(name, "Bowler") || Has(name, "TopHat") || Has(name, "Ladies") || Has(name, "Crown") || Has(name, "Coronet") || Has(name, "Stellic"))
            {
                return "tall";
            }
            if (Has(name, "Hood") || Has(name, "Veil") || Has(name, "Burka") || Has(name, "Wrap") || Has(name, "Slicecap") || Has(name, "Collar"))
            {
                return "hood";
            }
            if (Has(name, "Mask") || Has(name, "Visage"))
            {
                return fullHead ? "helmet" : "cap";
            }
            return "cap";
        }
    }
}
