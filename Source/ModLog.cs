using Verse;

namespace IsoRim
{
    // Log lines for working on the mod. Players never see them: they only appear with the game's
    // development mode on. Real errors still go to the log as errors.
    public static class ModLog
    {
        public static void Debug(string text)
        {
            if (Prefs.DevMode)
            {
                Log.Message(text);
            }
        }

        public static void Warn(string text)
        {
            if (Prefs.DevMode)
            {
                Log.Warning(text);
            }
        }
    }
}
