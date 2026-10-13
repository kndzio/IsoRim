// Unity editor script: builds the shader bundle IsoRim loads for exact (LUT) colour grading.
// Menu: IsoRim > Build shader bundles. The files land in this project's ShaderBundles folder; copy
// them into the mod's Shaders folder.
using System.IO;
using UnityEditor;

public static class BuildIsoRimShaders
{
    [MenuItem("IsoRim/Build shader bundles")]
    public static void Build()
    {
        Make(BuildTarget.StandaloneWindows64, "isorimshaders");
        Make(BuildTarget.StandaloneOSX, "isorimshaders_mac");
        Make(BuildTarget.StandaloneLinux64, "isorimshaders_linux");
        EditorUtility.RevealInFinder("ShaderBundles");
    }

    private static void Make(BuildTarget target, string name)
    {
        string dir = Path.Combine("ShaderBundles", target.ToString());
        Directory.CreateDirectory(dir);
        AssetBundleBuild build = new AssetBundleBuild();
        build.assetBundleName = name;
        build.assetNames = new[] { "Assets/IsoRim/IsoRim_LUT.shader" };
        BuildPipeline.BuildAssetBundles(dir, new[] { build }, BuildAssetBundleOptions.None, target);
        File.Copy(Path.Combine(dir, name), Path.Combine("ShaderBundles", name), true);
    }
}
