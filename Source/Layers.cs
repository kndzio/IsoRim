using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using RimWorld;
using UnityEngine;
using Verse;

namespace IsoRim
{
    // Two extra layers the game adds to every 17 x 17 block of the map by itself (it makes one of
    // every SectionLayer there is). Both draw nothing unless the 3D view is on.

    // ------------------------------------------------------------------ water

    // Water in the mod's own style, painted like the pools in the marsh ground: dark teal that
    // shades smoothly from a little lighter at the bank to darker out in the deep, with no lines
    // anywhere. Over it a see-through layer of soft ripples drifts and sways on still water, and
    // long streaks run downstream on rivers; both are moved every frame while they are on screen.
    [StaticConstructorOnStartup]
    public class SectionLayer_IsoRimWater : SectionLayer
    {
        private const int Reach = 3;   // how far from the shore the colour keeps getting deeper, in cells

        // From the shore outward, then the deep.
        private static readonly Color[] Bands =
        {
            new Color(0.272f, 0.385f, 0.400f),
            new Color(0.240f, 0.345f, 0.362f),
            new Color(0.212f, 0.308f, 0.325f),
            new Color(0.194f, 0.286f, 0.305f),
            new Color(0.178f, 0.266f, 0.288f),
            new Color(0.162f, 0.246f, 0.272f),
        };

        private static readonly IntVec3[] Side = { IntVec3.South, IntVec3.East, IntVec3.North, IntVec3.West };

        private static MethodInfo waterMovement;
        private static bool lookedMovement;
        private static Material ripples;
        private static Material flow;
        private static bool triedWaves;

        private int[] dist;
        private int[] deep;
        private int distW;
        private int distH;
        private CellRect distRect;

        // The moving layer: kept by this block itself (not part of the game's mesh) because its
        // texture coordinates are slid along every frame.
        private Mesh waveMesh;
        private readonly List<Vector3> waveVerts = new List<Vector3>();
        private readonly List<Vector2> waveBase = new List<Vector2>();
        private readonly List<Vector2> waveUV = new List<Vector2>();
        private readonly List<int> waveTris = new List<int>();
        private readonly List<Vector3> flowVerts = new List<Vector3>();
        private readonly List<Vector2> flowBase = new List<Vector2>();
        private readonly List<Vector2> flowUV = new List<Vector2>();
        private readonly List<int> flowTris = new List<int>();
        private Mesh flowMesh;

        public SectionLayer_IsoRimWater(Section section) : base(section)
        {
            MapSections.SetChangeFlags(this, "Terrain");
        }

        public override bool Visible
        {
            get { return View3D.Ready && IsoRimMod.Settings.waterStyle; }
        }

        public override void Regenerate()
        {
            ClearSubMeshes(MeshParts.All);
            waveVerts.Clear();
            waveBase.Clear();
            waveTris.Clear();
            flowVerts.Clear();
            flowBase.Clear();
            flowTris.Clear();
            if (View3D.Active && IsoRimMod.Settings.waterStyle && R3DMaterials.WaterOverlay != null)
            {
                try
                {
                    Build();
                }
                catch (Exception e)
                {
                    Log.ErrorOnce("[IsoRim] Drawing the water failed: " + e, 93611110);
                }
            }
            FinalizeMesh(MeshParts.All);
            waveMesh = Fill(waveMesh, waveVerts, waveBase, waveTris, "IsoRim_Ripples");
            flowMesh = Fill(flowMesh, flowVerts, flowBase, flowTris, "IsoRim_Flow");
        }

        private static Mesh Fill(Mesh mesh, List<Vector3> verts, List<Vector2> uvs, List<int> tris, string name)
        {
            if (verts.Count == 0)
            {
                if (mesh != null)
                {
                    mesh.Clear();
                }
                return mesh;
            }
            if (mesh == null)
            {
                mesh = new Mesh();
                mesh.name = name;
                mesh.MarkDynamic();
            }
            mesh.Clear();
            mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
            mesh.SetVertices(verts);
            mesh.SetUVs(0, uvs);
            mesh.SetTriangles(tris, 0);
            mesh.RecalculateBounds();
            return mesh;
        }

        public override void DrawLayer()
        {
            if (!Visible)
            {
                return;
            }
            base.DrawLayer();
            if (!IsoRimMod.Settings.effects3D)
            {
                return;
            }
            LoadWaves();
            Map map = Map;
            float glow = map != null && map.skyManager != null ? Mathf.Lerp(0.25f, 1f, map.skyManager.CurSkyGlow) : 1f;
            float t = Find.TickManager != null ? Find.TickManager.TicksGame / 60f : Time.time;
            if (ripples != null && waveMesh != null && waveVerts.Count > 0)
            {
                // still water: a slow drift with a gentle side-to-side sway
                Vector2 shift = new Vector2(t * 0.012f + 0.035f * Mathf.Sin(t * 0.45f), t * 0.008f + 0.025f * Mathf.Sin(t * 0.31f + 1.3f));
                Slide(waveMesh, waveBase, waveUV, shift);
                ripples.color = new Color(glow, glow, glow, 1f);
                Graphics.DrawMesh(waveMesh, Matrix4x4.identity, ripples, 0);
            }
            if (flow != null && flowMesh != null && flowVerts.Count > 0)
            {
                // running water: streaks carried downstream
                Slide(flowMesh, flowBase, flowUV, new Vector2(0.02f * Mathf.Sin(t * 0.7f), -t * 0.22f));
                flow.color = new Color(glow, glow, glow, 1f);
                Graphics.DrawMesh(flowMesh, Matrix4x4.identity, flow, 0);
            }
        }

        private static void Slide(Mesh mesh, List<Vector2> baseUV, List<Vector2> uv, Vector2 shift)
        {
            uv.Clear();
            for (int i = 0; i < baseUV.Count; i++)
            {
                uv.Add(baseUV[i] + shift);
            }
            mesh.SetUVs(0, uv);
        }

        private static void LoadWaves()
        {
            if (triedWaves)
            {
                return;
            }
            triedWaves = true;
            ripples = WaveMaterial("IsoRim/Water/Ripples", 3053);
            flow = WaveMaterial("IsoRim/Water/Flow", 3054);
        }

        private static Material WaveMaterial(string path, int queue)
        {
            Texture2D tex = R3DTextures.Get(path);
            if (tex == null)
            {
                return null;
            }
            Material m = new Material(ShaderDatabase.Transparent);
            m.name = "IsoRim_" + path.Substring(path.LastIndexOf('/') + 1);
            m.mainTexture = tex;
            m.renderQueue = queue;
            return m;
        }

        // Open water the mod draws.
        public static bool IsWater(Map map, IntVec3 c)
        {
            if (!c.InBounds(map))
            {
                return true;   // the sea runs on past the edge of the map
            }
            return Ground.IsWater(map.terrainGrid.TerrainAt(c));
        }

        // Land for the purpose of a shore: not water, and not a bridge over water either.
        private static bool IsShore(Map map, IntVec3 c)
        {
            if (!c.InBounds(map))
            {
                return false;
            }
            TerrainDef top = map.terrainGrid.TerrainAt(c);
            if (Ground.IsWater(top))
            {
                return false;
            }
            TerrainDef under = map.terrainGrid.UnderTerrainAt(c);
            return !Ground.IsWater(under);
        }

        private static int DepthOf(TerrainDef t)
        {
            string n = t != null ? (t.defName ?? "") : "";
            if (n.IndexOf("ChestDeep", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                return 1;
            }
            if (n.IndexOf("Deep", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                return 2;
            }
            return 0;
        }

        private static bool IsMoving(TerrainDef t)
        {
            return t != null && t.defName != null && t.defName.IndexOf("Moving", StringComparison.OrdinalIgnoreCase) >= 0;
        }

        // How far each cell in and round this block is from the nearest shore (up to Reach + 1;
        // 0 on land), and how deep its water is.
        private void Measure(Map map, CellRect rect)
        {
            distRect = rect.ExpandedBy(2);
            distW = distRect.Width;
            distH = distRect.Height;
            if (dist == null || dist.Length < distW * distH)
            {
                dist = new int[distW * distH];
                deep = new int[distW * distH];
            }
            for (int z = 0; z < distH; z++)
            {
                for (int x = 0; x < distW; x++)
                {
                    IntVec3 c = new IntVec3(distRect.minX + x, 0, distRect.minZ + z);
                    int d = 0;
                    int dp = 0;
                    if (IsWater(map, c))
                    {
                        d = Reach + 1;
                        for (int dz = -Reach; dz <= Reach && d > 1; dz++)
                        {
                            for (int dx = -Reach; dx <= Reach; dx++)
                            {
                                int r = Math.Max(Math.Abs(dx), Math.Abs(dz));
                                if (r < d && r > 0 && IsShore(map, new IntVec3(c.x + dx, 0, c.z + dz)))
                                {
                                    d = r;
                                }
                            }
                        }
                        dp = c.InBounds(map) ? DepthOf(map.terrainGrid.TerrainAt(c)) : 2;
                    }
                    dist[z * distW + x] = d;
                    deep[z * distW + x] = dp;
                }
            }
        }

        private int DistAt(int x, int z)
        {
            int i = x - distRect.minX, j = z - distRect.minZ;
            return i < 0 || j < 0 || i >= distW || j >= distH ? Reach : dist[j * distW + i];
        }

        private int DeepAt(int x, int z)
        {
            int i = x - distRect.minX, j = z - distRect.minZ;
            return i < 0 || j < 0 || i >= distW || j >= distH ? 0 : deep[j * distW + i];
        }

        // The water's colour at a cell corner: from how far the four cells round it are from the
        // shore and how deep they are, so neighbouring cells always agree and the colour flows on
        // smoothly from one to the next.
        private Color CornerColour(int cx, int cz)
        {
            float d = (DistAt(cx - 1, cz - 1) + DistAt(cx, cz - 1) + DistAt(cx - 1, cz) + DistAt(cx, cz)) * 0.25f;
            float dp = (DeepAt(cx - 1, cz - 1) + DeepAt(cx, cz - 1) + DeepAt(cx - 1, cz) + DeepAt(cx, cz)) * 0.25f;
            float index = Mathf.Clamp(d * 0.85f + dp, 0f, Bands.Length - 1.001f);
            int i = Mathf.FloorToInt(index);
            return Color.Lerp(Bands[i], Bands[i + 1], index - i);
        }

        private void Build()
        {
            Map map = Map;
            CellRect rect = section.CellRect;
            LayerSubMesh sm = MeshWriter.Sub(this, R3DMaterials.WaterOverlay);
            if (sm == null)
            {
                return;
            }
            Measure(map, rect);
            float y = AltitudeLayer.Terrain.AltitudeFor() + 0.012f;
            float yWaves = y + 0.004f;

            foreach (IntVec3 c in rect)
            {
                if (sm.verts.Count + 16 > MeshWriter.MaxVerts)
                {
                    break;
                }
                if (IsShore(map, c))
                {
                    RoundInnerCorners(map, sm, c, y);
                    continue;
                }
                if (!c.InBounds(map) || !IsWater(map, c))
                {
                    continue;
                }
                Color sw = CornerColour(c.x, c.z);
                Color nw = CornerColour(c.x, c.z + 1);
                Color ne = CornerColour(c.x + 1, c.z + 1);
                Color se = CornerColour(c.x + 1, c.z);
                MeshWriter.Quad(sm, new Vector3(c.x, y, c.z), new Vector3(c.x, y, c.z + 1), new Vector3(c.x + 1, y, c.z + 1), new Vector3(c.x + 1, y, c.z),
                    Opaque(sw), Opaque(nw), Opaque(ne), Opaque(se));

                // the moving layer over it
                TerrainDef t = map.terrainGrid.TerrainAt(c);
                if (IsMoving(t))
                {
                    Vector3 dir = Flow(map, c);
                    dir.y = 0f;
                    if (dir.sqrMagnitude < 1e-6f)
                    {
                        dir = Vector3.forward;
                    }
                    // the flow snapped to sixteen headings, so neighbouring cells share one pattern
                    float angle = Mathf.Round(Mathf.Atan2(dir.x, dir.z) / (Mathf.PI / 8f)) * (Mathf.PI / 8f);
                    Vector3 along = new Vector3(Mathf.Sin(angle), 0f, Mathf.Cos(angle));
                    Vector3 across = new Vector3(along.z, 0f, -along.x);
                    AddWaveQuad(flowVerts, flowBase, flowTris, c, yWaves, along, across, 0.30f);
                }
                else
                {
                    AddWaveQuad(waveVerts, waveBase, waveTris, c, yWaves, Vector3.forward, Vector3.right, 0.28f);
                }
            }
        }

        private static void AddWaveQuad(List<Vector3> verts, List<Vector2> uvs, List<int> tris, IntVec3 c, float y, Vector3 along, Vector3 across, float scale)
        {
            int start = verts.Count;
            for (int k = 0; k < 4; k++)
            {
                float x = c.x + (k == 2 || k == 3 ? 1 : 0);
                float z = c.z + (k == 1 || k == 2 ? 1 : 0);
                verts.Add(new Vector3(x, y, z));
                uvs.Add(new Vector2((x * across.x + z * across.z) * scale, (x * along.x + z * along.z) * scale));
            }
            tris.Add(start);
            tris.Add(start + 1);
            tris.Add(start + 2);
            tris.Add(start);
            tris.Add(start + 2);
            tris.Add(start + 3);
        }

        private static Color32 Opaque(Color c)
        {
            return R3DMaterials.Shaded(c, 1f);
        }

        // Where water wraps round a corner of land (water on both sides and across the diagonal),
        // the water is carried a little way into the land's corner, so the bank bends round in a
        // curve instead of a sharp square step. Its colour matches the water it joins exactly.
        private void RoundInnerCorners(Map map, LayerSubMesh sm, IntVec3 c, float y)
        {
            for (int sx = -1; sx <= 1; sx += 2)
            {
                for (int sz = -1; sz <= 1; sz += 2)
                {
                    IntVec3 diag = new IntVec3(c.x + sx, 0, c.z + sz);
                    if (!diag.InBounds(map) || !IsWater(map, new IntVec3(c.x + sx, 0, c.z)) || !IsWater(map, new IntVec3(c.x, 0, c.z + sz))
                        || !IsWater(map, diag))
                    {
                        continue;
                    }
                    int kx = c.x + (sx > 0 ? 1 : 0);
                    int kz = c.z + (sz > 0 ? 1 : 0);
                    float reach = 0.34f + 0.12f * Hashing.Unit(kx, kz, 7);
                    Color ck = CornerColour(kx, kz);
                    Color ca = Color.Lerp(ck, CornerColour(kx - sx, kz), reach);
                    Color cb = Color.Lerp(ck, CornerColour(kx, kz - sz), reach);
                    int start = sm.verts.Count;
                    sm.verts.Add(new Vector3(kx, y, kz));
                    sm.verts.Add(new Vector3(kx - sx * reach, y, kz));
                    sm.verts.Add(new Vector3(kx, y, kz - sz * reach));
                    sm.colors.Add(Opaque(ck));
                    sm.colors.Add(Opaque(ca));
                    sm.colors.Add(Opaque(cb));
                    for (int i = 0; i < 3; i++)
                    {
                        sm.uvs.Add(Vector3.zero);
                    }
                    sm.tris.Add(start);
                    sm.tris.Add(start + 1);
                    sm.tris.Add(start + 2);
                }
            }
        }

        // Which way the river runs at a cell, from the game's own record of it, or zero.
        private static Vector3 Flow(Map map, IntVec3 c)
        {
            if (!lookedMovement)
            {
                lookedMovement = true;
                Type info = AccessTools.TypeByName("Verse.WaterInfo");
                waterMovement = info != null ? AccessTools.Method(info, "GetWaterMovement", new[] { typeof(Vector3) }) : null;
            }
            if (waterMovement == null || map.waterInfo == null)
            {
                return Vector3.zero;
            }
            try
            {
                object v = waterMovement.Invoke(map.waterInfo, new object[] { c.ToVector3Shifted() });
                return v is Vector3 ? (Vector3)v : Vector3.zero;
            }
            catch (Exception)
            {
                waterMovement = null;
                return Vector3.zero;
            }
        }
    }

    // ------------------------------------------------------------------ walls and trees

    // Walls and natural rock, in a layer of their own. Lowering the walls near the pointer or
    // the colonists then only redraws the walls of a block, not every model in it, which is
    // what keeps sweeping the pointer across a big base smooth.
    public class SectionLayer_IsoRimWalls : SectionLayer
    {
        private static bool checkedTextures;
        private static bool haveTextures;

        public SectionLayer_IsoRimWalls(Section section) : base(section)
        {
            MapSections.SetChangeFlags(this, "Things", "Buildings");
        }

        public override bool Visible
        {
            get { return View3D.Ready; }
        }

        // Whether this layer draws the thing (a block with the mod's wall textures).
        public static bool Handles(Thing t)
        {
            if (!View3D.Active || !IsoRimMod.Settings.texturedWalls || !IsoRimMod.Settings.walls3D)
            {
                return false;
            }
            if (!checkedTextures)
            {
                checkedTextures = true;
                haveTextures = R3DTextures.Get("IsoRim/Walls/BricksTop") != null && R3DTextures.Get("IsoRim/Walls/RockTop") != null;
            }
            return haveTextures && t.def.drawerType != DrawerType.RealtimeOnly && Forms.For(t.def).form == Form3D.Block;
        }

        public override void Regenerate()
        {
            ClearSubMeshes(MeshParts.All);
            if (!View3D.Active)
            {
                return;
            }
            try
            {
                Map map = Map;
                foreach (IntVec3 c in section.CellRect)
                {
                    Building b = c.GetEdifice(map);
                    if (b == null || !Handles(b))
                    {
                        continue;
                    }
                    ThingForm form = Forms.For(b.def);
                    float height = WallBoxes.HeightFor(b, form.height);
                    GroundShadows.AroundBlock(this, b);
                    WallBoxes.PrintBlock(this, b, height);
                }
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Drawing the walls failed: " + e, 93611112);
            }
            FinalizeMesh(MeshParts.All);
        }
    }

    // Trees with a model, in a layer of their own for the same reason: thinning out the trees
    // near the pointer or the colonists only redraws the trees.
    public class SectionLayer_IsoRimTrees : SectionLayer
    {
        public SectionLayer_IsoRimTrees(Section section) : base(section)
        {
            MapSections.SetChangeFlags(this, "Things");
        }

        public override bool Visible
        {
            get { return View3D.Ready; }
        }

        public static bool Handles(Thing t)
        {
            Plant plant = t as Plant;
            return plant != null && View3D.Active && plant.def.plant != null && plant.def.plant.IsTree
                && Forms.For(plant.def).form == Form3D.Model && plant.def.drawerType != DrawerType.RealtimeOnly;
        }

        public override void Regenerate()
        {
            ClearSubMeshes(MeshParts.All);
            if (!View3D.Active)
            {
                return;
            }
            try
            {
                Map map = Map;
                foreach (IntVec3 c in section.CellRect)
                {
                    List<Thing> things = map.thingGrid.ThingsListAtFast(c);
                    for (int i = 0; i < things.Count; i++)
                    {
                        Thing t = things[i];
                        if (t.Position != c || !Handles(t))
                        {
                            continue;
                        }
                        ThingForm form = Forms.For(t.def);
                        ModelBaker.Bake(this, t, form.model, Forms.BaseUnder(t, false));
                    }
                }
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Drawing the trees failed: " + e, 93611113);
            }
            FinalizeMesh(MeshParts.All);
        }
    }

    // ------------------------------------------------------------------ roofs

    // Roofs as solid lids at the top of the walls, switched on and off as a whole with the button in
    // the corner of the screen. A built roof is laid in rows of slates and runs out over the walls
    // that hold it up, with a short overhang and a fascia board round the edge; a natural rock roof
    // over a cave is a plain stone lid level with the rock round it.
    [StaticConstructorOnStartup]
    public class SectionLayer_IsoRimRoofs : SectionLayer
    {
        private const float Rise = 0.03f;       // a built roof sits this far above the wall tops, in cells
        private const float Overhang = 0.07f;
        private const float Fascia = 0.10f;
        private const int Rows = 3;              // rows of slates per cell
        private static readonly Color Slate = new Color(0.50f, 0.45f, 0.42f);
        private static readonly Color Stone = new Color(0.43f, 0.42f, 0.41f);
        private static readonly IntVec3[] Side = { IntVec3.South, IntVec3.East, IntVec3.North, IntVec3.West };
        private static readonly int[] AX = { 0, 1, 1, 0 };
        private static readonly int[] AZ = { 0, 0, 1, 1 };
        private static readonly int[] BX = { 1, 1, 0, 0 };
        private static readonly int[] BZ = { 0, 1, 1, 0 };

        private static MaterialPropertyBlock block;
        private static int colorId = -1;
        private readonly bool[] open = new bool[4];

        public SectionLayer_IsoRimRoofs(Section section) : base(section)
        {
            MapSections.SetChangeFlags(this, "Roofs", "Buildings");
        }

        public override bool Visible
        {
            get { return View3D.Ready && IsoRimMod.Settings.showRoofs; }
        }

        public override void Regenerate()
        {
            ClearSubMeshes(MeshParts.All);
            if (!View3D.Active || !IsoRimMod.Settings.showRoofs || R3DMaterials.Roof == null)
            {
                return;
            }
            try
            {
                Build();
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Drawing the roofs failed: " + e, 93611111);
            }
            FinalizeMesh(MeshParts.All);
        }

        // Drawn with the daylight: roofs are not darkened by the rooms under them, so they dim at night by themselves.
        public override void DrawLayer()
        {
            if (!Visible)
            {
                return;
            }
            if (block == null)
            {
                block = new MaterialPropertyBlock();
                colorId = Shader.PropertyToID("_Color");
            }
            Map map = Map;
            float glow = map != null && map.skyManager != null ? Mathf.Lerp(0.30f, 1f, map.skyManager.CurSkyGlow) : 1f;
            for (int i = 0; i < subMeshes.Count; i++)
            {
                LayerSubMesh sm = subMeshes[i];
                if (sm.finalized && !sm.disabled)
                {
                    // The textured courses carry their colour and shading in the material's colour,
                    // which the dimming has to keep; the plain parts are coloured per corner.
                    Color baseColor;
                    if (!textureColors.TryGetValue(sm.material, out baseColor))
                    {
                        baseColor = Color.white;
                    }
                    int bin;
                    if (textureBins.TryGetValue(sm.material, out bin))
                    {
                        baseColor *= Mathf.Min(1.1f, R3DMaterials.BinShade(bin, 0) * 1.05f);
                    }
                    block.SetColor(colorId, new Color(baseColor.r * glow, baseColor.g * glow, baseColor.b * glow, 1f));
                    Graphics.DrawMesh(sm.mesh, Matrix4x4.identity, sm.material, 0, null, 0, block);
                }
            }
        }

        // 0: no lid here. 1: a built roof (or a wall under the edge of one). 2: a natural rock roof over open ground.
        private static int LidKind(Map map, IntVec3 c)
        {
            if (!c.InBounds(map) || Cutaway.RoofOpen(map, c))
            {
                return 0;
            }
            RoofDef roof = map.roofGrid.RoofAt(c);
            Building b = c.GetEdifice(map);
            bool solidBlock = b != null && Forms.For(b.def).form == Form3D.Block;
            bool natural = solidBlock && b.def.building != null && b.def.building.isNaturalRock;
            if (roof != null)
            {
                if (!roof.isNatural)
                {
                    return 1;
                }
                return solidBlock ? 0 : 2;
            }
            if (natural || b == null || !(solidBlock || b is Building_Door || b.def.fillPercent >= 0.99f))
            {
                return 0;
            }
            // A wall, door or anything set into a wall (coolers, vents) with a built roof beside it
            // carries the edge of that roof.
            for (int i = 0; i < 8; i++)
            {
                IntVec3 n = c + GenAdj.AdjacentCells[i];
                if (n.InBounds(map))
                {
                    RoofDef r = map.roofGrid.RoofAt(n);
                    if (r != null && !r.isNatural)
                    {
                        return 1;
                    }
                }
            }
            return 0;
        }

        // Roof colours to pick from in the options: slate, terracotta, thatch, tin.
        public static readonly Color[] Styles =
        {
            new Color(0.40f, 0.42f, 0.47f),
            new Color(0.68f, 0.36f, 0.26f),
            new Color(0.72f, 0.60f, 0.36f),
            new Color(0.56f, 0.60f, 0.60f),
        };
        public static readonly string[] StyleNames = { "Slate", "Terracotta", "Thatch", "Tin" };

        private static readonly Dictionary<Material, Color> textureColors = new Dictionary<Material, Color>();
        private static readonly Dictionary<int, Material> textureMats = new Dictionary<int, Material>();
        private const int ShadeSteps = 14;

        // The textured material for a roof colour at one brightness, or null if the texture is missing.
        // Drawn just after the plain roof underneath it, so it lies over it.
        // A roof texture for one direction group (see R3DMaterials.Lit). Its brightness is set
        // each time it is drawn from where the sun is then, so roofs light smoothly too.
        private static readonly Dictionary<Material, int> textureBins = new Dictionary<Material, int>();

        private static Material TextureMaterial(int style, int bin)
        {
            int level = bin;
            int key = style * 32 + level;
            Material m;
            if (textureMats.TryGetValue(key, out m))
            {
                return m;
            }
            Texture2D tex = R3DTextures.Get("IsoRim/Roofs/" + StyleNames[style]);
            if (tex != null)
            {
                m = new Material(ShaderDatabase.Cutout);
                m.name = "IsoRim_Roof_" + StyleNames[style] + level;
                m.mainTexture = tex;
                Color c = Styles[style] * 1.25f;
                c.a = 1f;
                m.color = c;
                m.renderQueue = 3601;
                textureColors[m] = c;
                textureBins[m] = bin;
            }
            textureMats[key] = m;
            return m;
        }

        private const int MaxLevel = 4;          // a roof rises for at most this many cells in from its edge
        public const int Reach = MaxLevel + 2;   // how far a change to one roof cell can alter the roof around it
        private const float Pitch = 0.55f;       // how much it rises per cell, in cells

        private int[] kinds;
        private int[] levels;
        private CellRect area;

        private int KindAt(int x, int z)
        {
            int i = x - area.minX, j = z - area.minZ;
            if (i < 0 || j < 0 || i >= area.Width || j >= area.Height)
            {
                return 0;
            }
            return kinds[j * area.Width + i];
        }

        // How many cells in from the roof's edge a built-roof cell is (1 at the edge), up to MaxLevel + 1.
        private int LevelAt(int x, int z)
        {
            int i = x - area.minX, j = z - area.minZ;
            if (i < 0 || j < 0 || i >= area.Width || j >= area.Height)
            {
                return 0;
            }
            return levels[j * area.Width + i];
        }

        // The height step at a cell corner: the lowest of the four cells round it, so the roof
        // meets its edge at level 0 and rises one step for every cell inward, like a hipped roof.
        private int CornerLevel(int cx, int cz)
        {
            int l = Mathf.Min(Mathf.Min(LevelAt(cx - 1, cz - 1), LevelAt(cx, cz - 1)), Mathf.Min(LevelAt(cx - 1, cz), LevelAt(cx, cz)));
            return Mathf.Min(l, MaxLevel);
        }

        private void Build()
        {
            Map map = Map;
            LayerSubMesh sm = MeshWriter.Sub(this, R3DMaterials.Roof);
            if (sm == null)
            {
                return;
            }
            float squash = View3D.Squash;
            float wall = View3D.WallHeight;
            Color roofCol = Styles[Mathf.Clamp(IsoRimMod.Settings.roofStyle, 0, Styles.Length - 1)];

            // What lies in and round this block: the kind of lid in each cell, then how far in
            // from the edge each built-roof cell is.
            area = section.CellRect.ExpandedBy(MaxLevel + 2);
            int n = area.Width * area.Height;
            if (kinds == null || kinds.Length < n)
            {
                kinds = new int[n];
                levels = new int[n];
            }
            for (int j = 0; j < area.Height; j++)
            {
                for (int i = 0; i < area.Width; i++)
                {
                    kinds[j * area.Width + i] = LidKind(map, new IntVec3(area.minX + i, 0, area.minZ + j));
                }
            }
            for (int j = 0; j < area.Height; j++)
            {
                for (int i = 0; i < area.Width; i++)
                {
                    int x = area.minX + i, z = area.minZ + j;
                    int d = 0;
                    if (kinds[j * area.Width + i] == 1)
                    {
                        d = MaxLevel + 1;
                        for (int r = 1; r <= MaxLevel && d > MaxLevel; r++)
                        {
                            for (int k = -r; k <= r && d > MaxLevel; k++)
                            {
                                if (KindAt(x + k, z - r) != 1 || KindAt(x + k, z + r) != 1 || KindAt(x - r, z + k) != 1 || KindAt(x + r, z + k) != 1)
                                {
                                    d = r;
                                }
                            }
                        }
                    }
                    levels[j * area.Width + i] = d;
                }
            }

            Vector3[] p = new Vector3[4];
            foreach (IntVec3 c in section.CellRect)
            {
                int kind = KindAt(c.x, c.z);
                if (kind == 0)
                {
                    continue;
                }
                if (sm.verts.Count + 64 > MeshWriter.MaxVerts)
                {
                    break;
                }
                for (int f = 0; f < 4; f++)
                {
                    open[f] = KindAt(c.x + Side[f].x, c.z + Side[f].z) != kind;
                }

                if (kind == 2)
                {
                    // A rock roof over a cave: a plain stone lid level with the rock round it.
                    float y = (wall - 0.005f) / squash;
                    float tone = 0.93f + 0.10f * Hashing.Unit(c.x, c.z, 62);
                    MeshWriter.Quad(sm, new Vector3(c.x, y, c.z), new Vector3(c.x, y, c.z + 1), new Vector3(c.x + 1, y, c.z + 1), new Vector3(c.x + 1, y, c.z),
                        R3DMaterials.Shaded(Stone, tone));
                    continue;
                }

                // A built roof: each corner at its own height, the cell split into two sloping facets
                // along whichever diagonal makes the ridge or valley.
                for (int k = 0; k < 4; k++)
                {
                    int cx = c.x + AX[k == 0 ? 0 : (k == 1 ? 3 : (k == 2 ? 2 : 1))];
                    int cz = c.z + AZ[k == 0 ? 0 : (k == 1 ? 3 : (k == 2 ? 2 : 1))];
                    float h = wall + Rise + Pitch * CornerLevel(cx, cz);
                    p[k] = new Vector3(cx, h, cz);   // in cells; corners SW, NW, NE, SE
                }
                bool alongSwNe = Mathf.Abs(p[0].y - p[2].y) >= Mathf.Abs(p[1].y - p[3].y);
                int style = Mathf.Clamp(IsoRimMod.Settings.roofStyle, 0, Styles.Length - 1);
                if (alongSwNe)
                {
                    Facet(this, sm, p[0], p[1], p[2], roofCol, c, style);
                    Facet(this, sm, p[0], p[2], p[3], roofCol, c, style);
                }
                else
                {
                    Facet(this, sm, p[0], p[1], p[3], roofCol, c, style);
                    Facet(this, sm, p[1], p[2], p[3], roofCol, c, style);
                }

                // Round the open edges: the eaves run out a little and down, with a fascia board
                // under them and a dark line along the edge.
                for (int f = 0; f < 4; f++)
                {
                    if (!open[f])
                    {
                        continue;
                    }
                    Vector3 outward = Side[f].ToVector3();
                    Vector3 a = new Vector3(c.x + AX[f], 0f, c.z + AZ[f]);
                    Vector3 b = new Vector3(c.x + BX[f], 0f, c.z + BZ[f]);
                    float edge = (wall + Rise) / squash;
                    float eave = (wall + Rise - Overhang * Pitch) / squash;
                    float bottom = (wall + Rise - Overhang * Pitch - Fascia) / squash;
                    Vector3 ao = a + outward * Overhang;
                    Vector3 bo = b + outward * Overhang;
                    // carry the eave round outside corners
                    if (open[(f + 3) % 4])
                    {
                        ao += Side[(f + 3) % 4].ToVector3() * Overhang;
                    }
                    if (open[(f + 1) % 4])
                    {
                        bo += Side[(f + 1) % 4].ToVector3() * Overhang;
                    }
                    Color32 under = R3DMaterials.Shaded(roofCol, 0.72f);
                    MeshWriter.Quad(sm, new Vector3(a.x, edge, a.z), new Vector3(ao.x, eave, ao.z), new Vector3(bo.x, eave, bo.z), new Vector3(b.x, edge, b.z), under);
                    Color32 face = R3DMaterials.Shaded(roofCol, 0.46f);
                    MeshWriter.Quad(sm, new Vector3(ao.x, bottom, ao.z), new Vector3(ao.x, eave, ao.z), new Vector3(bo.x, eave, bo.z), new Vector3(bo.x, bottom, bo.z), face);
                    Color32 line = R3DMaterials.Shaded(roofCol, 0.28f);
                    float lift = 0.002f / squash;
                    Vector3 inner = outward * -0.04f;
                    MeshWriter.Quad(sm, new Vector3(ao.x, eave + lift, ao.z), new Vector3(ao.x + inner.x, eave + lift, ao.z + inner.z),
                        new Vector3(bo.x + inner.x, eave + lift, bo.z + inner.z), new Vector3(bo.x, eave + lift, bo.z), line);
                }
            }
        }

        // One sloping facet of a built roof, given in cells, lit by the sun: a plain copy that hides
        // what is under the roof, and over it the roof's texture, laid so its courses run along
        // the slope's contour (across the way the rain runs off).
        private static void Facet(SectionLayer layer, LayerSubMesh sm, Vector3 a, Vector3 b, Vector3 c, Color col, IntVec3 cell, int style)
        {
            float squash = View3D.Squash;
            Vector3 normal = Vector3.Cross(b - a, c - a).normalized;
            if (normal.y < 0f)
            {
                normal = -normal;
            }
            Color32 plain = R3DMaterials.Shaded(col, 0.85f);
            float under = 0.012f / squash;
            AddTri(sm, new Vector3(a.x, a.y / squash - under, a.z), new Vector3(b.x, b.y / squash - under, b.z), new Vector3(c.x, c.y / squash - under, c.z),
                plain, Vector2.zero, Vector2.zero, Vector2.zero);

            Material mat = TextureMaterial(style, R3DMaterials.BinOf(normal));
            LayerSubMesh tm = mat != null ? MeshWriter.Sub(layer, mat) : null;
            if (tm == null || tm.verts.Count + 3 > MeshWriter.MaxVerts)
            {
                return;
            }
            // Which way the facet runs downhill, snapped to the map's axes so neighbouring facets
            // facing the same way share one continuous pattern; a level facet uses north-south.
            Vector3 down = new Vector3(normal.x, 0f, normal.z);
            if (down.sqrMagnitude < 0.0025f)
            {
                down = new Vector3(0f, 0f, -1f);
            }
            else if (Mathf.Abs(down.x) > Mathf.Abs(down.z))
            {
                down = new Vector3(Mathf.Sign(down.x), 0f, 0f);
            }
            else
            {
                down = new Vector3(0f, 0f, Mathf.Sign(down.z));
            }
            Vector3 across = new Vector3(down.z, 0f, -down.x);
            Color32 white = new Color32(255, 255, 255, 255);
            AddTri(tm, new Vector3(a.x, a.y / squash, a.z), new Vector3(b.x, b.y / squash, b.z), new Vector3(c.x, c.y / squash, c.z), white,
                RoofUV(a, down, across), RoofUV(b, down, across), RoofUV(c, down, across));
        }

        // One copy of a roof texture covers two cells; v climbs the slope.
        private static Vector2 RoofUV(Vector3 p, Vector3 down, Vector3 across)
        {
            float u = (p.x * across.x + p.z * across.z) * 0.5f;
            float v = (-(p.x * down.x + p.z * down.z) + p.y) * 0.5f;
            return new Vector2(u, v);
        }

        private static void AddTri(LayerSubMesh sm, Vector3 a, Vector3 b, Vector3 c, Color32 color, Vector2 ua, Vector2 ub, Vector2 uc)
        {
            int start = sm.verts.Count;
            sm.verts.Add(a);
            sm.verts.Add(b);
            sm.verts.Add(c);
            sm.uvs.Add(new Vector3(ua.x, ua.y, 0f));
            sm.uvs.Add(new Vector3(ub.x, ub.y, 0f));
            sm.uvs.Add(new Vector3(uc.x, uc.y, 0f));
            for (int i = 0; i < 3; i++)
            {
                sm.colors.Add(color);
            }
            sm.tris.Add(start);
            sm.tris.Add(start + 1);
            sm.tris.Add(start + 2);
        }

        // The ends of side f of the lid rectangle, going round anticlockwise seen from above.
        private static Vector3 Corner(int f, bool first, float x0, float x1, float z0, float z1)
        {
            int cx = first ? AX[f] : BX[f];
            int cz = first ? AZ[f] : BZ[f];
            return new Vector3(cx == 0 ? x0 : x1, 0f, cz == 0 ? z0 : z1);
        }
    }

    // Switching the roofs on and off.
    public static class Roofs
    {
        public static void Toggle()
        {
            Set(!IsoRimMod.Settings.showRoofs);
        }

        public static void Set(bool on)
        {
            IsoRimSettings st = IsoRimMod.Settings;
            if (st.showRoofs == on)
            {
                return;
            }
            st.showRoofs = on;
            IsoRimMod.Save();
            Rebuild();
        }

        // Redraws the roofs of every map, the part on screen first.
        public static void Rebuild()
        {
            if (Current.ProgramState != ProgramState.Playing || Find.Maps == null)
            {
                return;
            }
            foreach (Map map in Find.Maps)
            {
                MapSections.QueueAll(map, typeof(SectionLayer_IsoRimRoofs), map == Find.CurrentMap);
            }
        }
    }
}

namespace IsoRim
{
    // Scratches, cracks, chips and dents on damaged buildings, standing in for the game's flat
    // damage overlay (which would lie on the ground under a 3D model). Marks sit on the real
    // surfaces: across the faces of a model, on the cap and open sides of a wall, and on the
    // top of anything raised from its sprite. More damage, more marks. Redrawn whenever the
    // game says a building's damage has changed.
    public class SectionLayer_IsoRimDamage : SectionLayer
    {
        private const string TexturePath = "IsoRim/Damage/Marks";
        private static Material material;
        private static bool tried;

        public SectionLayer_IsoRimDamage(Section section) : base(section)
        {
            MapSections.SetChangeFlags(this, "BuildingsDamage", "Buildings");
        }

        public override bool Visible
        {
            get { return View3D.Ready && IsoRimMod.Settings.damage3D; }
        }

        private static Material Mat
        {
            get
            {
                if (!tried)
                {
                    tried = true;
                    material = R3DTextures.MaterialFor(TexturePath, new Color(0.9f, 0.9f, 0.9f, 1f));
                }
                return material;
            }
        }

        public override void Regenerate()
        {
            ClearSubMeshes(MeshParts.All);
            if (!View3D.Active || !IsoRimMod.Settings.damage3D || Mat == null)
            {
                return;
            }
            try
            {
                Map map = Map;
                foreach (IntVec3 c in section.CellRect)
                {
                    List<Thing> things = map.thingGrid.ThingsListAtFast(c);
                    for (int i = 0; i < things.Count; i++)
                    {
                        Building b = things[i] as Building;
                        if (b == null || b.Position != c || !b.def.useHitPoints || b.MaxHitPoints <= 0 || b.HitPoints >= b.MaxHitPoints)
                        {
                            continue;
                        }
                        float hurt = 1f - (float)b.HitPoints / b.MaxHitPoints;
                        int area = b.def.size.x * b.def.size.z;
                        int marks = Mathf.Clamp(Mathf.CeilToInt(hurt * (3f + area * 1.5f)), 1, 14);
                        MarkThing(b, marks);
                    }
                }
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Drawing damage marks failed: " + e, 93611150);
            }
            FinalizeMesh(MeshParts.All);
        }

        private void MarkThing(Building b, int marks)
        {
            ThingForm form = Forms.For(b.def);
            int id = b.thingIDNumber;
            switch (form.form)
            {
                case Form3D.Model:
                    if (form.model != null)
                    {
                        ModelBaker.DamageMarks = marks;
                        try
                        {
                            ModelBaker.Bake(this, b, form.model, 0f);
                        }
                        finally
                        {
                            ModelBaker.DamageMarks = 0;
                        }
                    }
                    break;

                case Form3D.Block:
                {
                    Map map = b.Map;
                    IntVec3 c = b.Position;
                    float h = WallBoxes.HeightFor(b, form.height);
                    for (int k = 0; k < marks; k++)
                    {
                        int face = (int)(Hashing.Unit(id, k, 61) * 5f);   // 0 the cap, 1 to 4 the sides
                        float u = 0.2f + 0.6f * Hashing.Unit(id, k, 67);
                        float v = 0.2f + 0.6f * Hashing.Unit(id, k, 71);
                        float size = 0.13f + 0.08f * Hashing.Unit(id, k, 73);
                        if (face == 0)
                        {
                            Mark(this, new Vector3(c.x + u, h + 0.006f, c.z + v), Vector3.up, size, id * 31 + k);
                            continue;
                        }
                        IntVec3 dir = GenAdj.CardinalDirections[face - 1];
                        if (WallBoxes.BlockHeightAt(map, c + dir) >= h - 0.01f)
                        {
                            continue;   // that side is up against another block
                        }
                        Vector3 n = dir.ToVector3();
                        Vector3 along = new Vector3(n.z, 0f, n.x);
                        Vector3 mid = new Vector3(c.x + 0.5f, 0f, c.z + 0.5f) + n * 0.506f + along * (u - 0.5f);
                        mid.y = h * v;
                        Mark(this, mid, n, size, id * 31 + k);
                    }
                    break;
                }

                case Form3D.Extruded:
                {
                    CellRect rect = b.OccupiedRect();
                    float top = form.height + 0.006f;
                    for (int k = 0; k < marks; k++)
                    {
                        float x = rect.minX + 0.2f + (rect.Width - 0.4f) * Hashing.Unit(id, k, 79);
                        float z = rect.minZ + 0.2f + (rect.Height - 0.4f) * Hashing.Unit(id, k, 83);
                        Mark(this, new Vector3(x, top, z), Vector3.up, 0.14f + 0.08f * Hashing.Unit(id, k, 89), id * 31 + k);
                    }
                    break;
                }
            }
        }

        // One square mark centred on at (x and z in cells, y the height in cells), lying on the
        // surface with the given outward normal, size cells across. seed picks which mark and
        // how it is turned. Returns false if there is no room in the mesh.
        public static bool Mark(SectionLayer layer, Vector3 at, Vector3 normal, float size, int seed)
        {
            Material mat = Mat;
            LayerSubMesh sm = mat != null ? MeshWriter.Sub(layer, mat) : null;
            if (sm == null || sm.verts.Count + 4 > MeshWriter.MaxVerts)
            {
                return false;
            }
            Vector3 n = normal.normalized;
            Vector3 u = Vector3.Cross(n, Mathf.Abs(n.y) > 0.9f ? Vector3.forward : Vector3.up).normalized;
            Vector3 v = Vector3.Cross(n, u);
            float spin = Hashing.Unit(seed, 5, 97) * Mathf.PI * 2f;
            Vector3 su = (u * Mathf.Cos(spin) + v * Mathf.Sin(spin)) * (size * 0.5f);
            Vector3 sv = (v * Mathf.Cos(spin) - u * Mathf.Sin(spin)) * (size * 0.5f);
            int cell = (int)(Hashing.Unit(seed, 9, 101) * 4f) & 3;
            float u0 = (cell % 2) * 0.5f;
            float v0 = (cell / 2) * 0.5f;
            float squash = View3D.Squash;
            MeshWriter.TexturedQuad(sm,
                Flat(at - su - sv, squash), Flat(at - su + sv, squash), Flat(at + su + sv, squash), Flat(at + su - sv, squash),
                new Vector2(u0, v0), new Vector2(u0, v0 + 0.5f), new Vector2(u0 + 0.5f, v0 + 0.5f), new Vector2(u0 + 0.5f, v0),
                new Color32(255, 255, 255, 255));
            return true;
        }

        private static Vector3 Flat(Vector3 apparent, float squash)
        {
            return new Vector3(apparent.x, apparent.y / squash, apparent.z);
        }
    }
}

namespace IsoRim
{
    // The edge of the map as a cut through the earth: round the outside of the map a face drops
    // a few cells below the ground, showing grass and topsoil over bands of clay and rock with
    // flecks of ore and a broken bottom edge, so the map reads as a diorama lifted out of the
    // ground rather than a flat sheet. Lit by the sun like the walls.
    public class SectionLayer_IsoRimEdge : SectionLayer
    {
        private const string TexturePath = "IsoRim/Edge/Strata";
        private const float Depth = 6f;          // cells the face drops below the ground
        private const float Repeat = 6f;         // cells across one copy of the texture

        public SectionLayer_IsoRimEdge(Section section) : base(section)
        {
        }

        public override bool Visible
        {
            get { return View3D.Ready && IsoRimMod.Settings.mapEdge3D; }
        }

        public override void Regenerate()
        {
            ClearSubMeshes(MeshParts.All);
            if (!View3D.Active || !IsoRimMod.Settings.mapEdge3D)
            {
                return;
            }
            try
            {
                Map map = Map;
                CellRect r = section.CellRect;
                int w = map.Size.x;
                int h = map.Size.z;
                float squash = View3D.Squash;
                float top = -0.002f / squash;
                float bottom = -Depth / squash;
                if (r.minZ == 0)
                {
                    Face(new Vector3(0f, 0f, -1f), r.minX, r.maxX + 1, top, bottom,
                        x => new Vector3(x, 0f, 0f), false);
                }
                if (r.maxZ == h - 1)
                {
                    Face(new Vector3(0f, 0f, 1f), r.minX, r.maxX + 1, top, bottom,
                        x => new Vector3(x, 0f, h), true);
                }
                if (r.minX == 0)
                {
                    Face(new Vector3(-1f, 0f, 0f), r.minZ, r.maxZ + 1, top, bottom,
                        z => new Vector3(0f, 0f, z), true);
                }
                if (r.maxX == w - 1)
                {
                    Face(new Vector3(1f, 0f, 0f), r.minZ, r.maxZ + 1, top, bottom,
                        z => new Vector3(w, 0f, z), false);
                }
            }
            catch (Exception e)
            {
                Log.ErrorOnce("[IsoRim] Drawing the edge of the map failed: " + e, 93611180);
            }
            FinalizeMesh(MeshParts.All);
        }

        // One side's stretch of face from a to b along the edge; flip runs the texture the other
        // way so it reads left to right from outside.
        private void Face(Vector3 normal, int a, int b, float top, float bottom, Func<float, Vector3> at, bool flip)
        {
            Vector3 f = View3D.GroundForward;
            if (normal.x * f.x + normal.z * f.z > -0.01f)
            {
                return;   // a side facing away from the camera: it would only show through the ground
            }
            Material mat = R3DMaterials.LitTexture(TexturePath, Color.white, R3DMaterials.BinOf(normal), 1);
            LayerSubMesh sm = mat != null ? MeshWriter.Sub(this, mat) : null;
            if (sm == null)
            {
                return;
            }
            for (int i = a; i < b; i++)
            {
                Vector3 p0 = at(i);
                Vector3 p1 = at(i + 1);
                float u0 = (flip ? -i : i) / Repeat;
                float u1 = (flip ? -(i + 1) : i + 1) / Repeat;
                // Wound both ways, so it shows whatever the shader culls; only the sides facing
                // the camera are built at all (see Regenerate).
                Color32 white = new Color32(255, 255, 255, 255);
                MeshWriter.TexturedQuad(sm,
                    new Vector3(p0.x, bottom, p0.z), new Vector3(p0.x, top, p0.z), new Vector3(p1.x, top, p1.z), new Vector3(p1.x, bottom, p1.z),
                    new Vector2(u0, 0f), new Vector2(u0, 1f), new Vector2(u1, 1f), new Vector2(u1, 0f), white);
                MeshWriter.TexturedQuad(sm,
                    new Vector3(p1.x, bottom, p1.z), new Vector3(p1.x, top, p1.z), new Vector3(p0.x, top, p0.z), new Vector3(p0.x, bottom, p0.z),
                    new Vector2(u1, 0f), new Vector2(u1, 1f), new Vector2(u0, 1f), new Vector2(u0, 0f), white);
            }
        }
    }
}
