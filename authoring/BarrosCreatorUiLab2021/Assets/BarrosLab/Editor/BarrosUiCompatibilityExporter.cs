using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace Barros.Creator.UiLab.Editor
{
    public static class BarrosUiCompatibilityExporter
    {
        private static readonly string[] SkinFiles = { "panel.png", "card.png", "button.png", "active.png", "primary.png" };

        [MenuItem("Barros/2 - Export Unity 2017-Compatible UI Pack")]
        public static void ExportCompatibilityPack()
        {
            string repoRoot = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
            string sourceRoot = Path.Combine(Application.dataPath, "BarrosLab", "Generated");
            string outputRoot = Path.Combine(repoRoot, "assets", "ui", "generated");
            Directory.CreateDirectory(outputRoot);

            StringBuilder manifestFiles = new StringBuilder();
            for (int i = 0; i < SkinFiles.Length; i++)
            {
                string source = Path.Combine(sourceRoot, SkinFiles[i]);
                if (!File.Exists(source)) throw new FileNotFoundException("Build the UI prototype first.", source);
                string destination = Path.Combine(outputRoot, SkinFiles[i]);
                File.Copy(source, destination, true);
                if (i > 0) manifestFiles.Append(",\n");
                manifestFiles.Append("    { \"name\": \"").Append(SkinFiles[i]).Append("\", \"sha256\": \"")
                    .Append(Sha256(destination)).Append("\" }");
            }

            string theme = "{\n" +
                "  \"schema_version\": 1,\n" +
                "  \"authoring_editor\": \"2021.3.45f2\",\n" +
                "  \"target_runtime\": \"Unity 2017.3.1p4\",\n" +
                "  \"format\": \"neutral-png-json\",\n" +
                "  \"virtual_size\": { \"width\": 640, \"height\": 1050 },\n" +
                "  \"protected_tab_count\": 5,\n" +
                "  \"corner_radius\": { \"panel\": 16, \"card\": 14, \"control\": 13 },\n" +
                "  \"colors\": {\n" +
                "    \"parchment\": \"#EFD6C7\", \"card\": \"#F7E0D1\", \"light\": \"#FDEDE3\",\n" +
                "    \"maroon\": \"#6E1F21\", \"red\": \"#AD292E\", \"ink\": \"#2E211F\"\n" +
                "  },\n" +
                "  \"files\": [\n" + manifestFiles + "\n  ]\n" +
                "}\n";
            File.WriteAllText(Path.Combine(outputRoot, "barros-ui-theme.json"), theme, new UTF8Encoding(false));
            AssetDatabase.Refresh();
            Debug.Log("BARROS_UI_EXPORT_OK output=" + outputRoot + " files=" + SkinFiles.Length + " format=png+json");
        }

        private static string Sha256(string path)
        {
            using (SHA256 hash = SHA256.Create())
            using (FileStream stream = File.OpenRead(path))
            {
                byte[] bytes = hash.ComputeHash(stream);
                StringBuilder text = new StringBuilder(bytes.Length * 2);
                foreach (byte value in bytes) text.Append(value.ToString("x2"));
                return text.ToString();
            }
        }
    }
}
