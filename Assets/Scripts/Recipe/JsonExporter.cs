using System;
using System.IO;
using System.Text;
using UnityEngine;

namespace creator_ui.Recipe
{
    public static class JsonExporter
    {
        // PC3 IngredientSize enum: Large=0, Medium=1, Small=2 (IngredientModel.cs:12-17)
        private static int SizeToInt(string size)
        {
            if (size == "Large") return 0;
            if (size == "Small") return 2;
            return 1;  // Medium default
        }

        public static void WriteFinal(RecipeData recipe, string outputPath)
        {
            var sb = new StringBuilder();
            sb.AppendLine("{");
            sb.AppendLine($"  \"ID\": \"{Guid.NewGuid()}\",");
            sb.AppendLine("  \"Ingredients\": [");
            if (recipe?.ingredients != null)
            {
                for (int i = 0; i < recipe.ingredients.Length; i++)
                {
                    var ing = recipe.ingredients[i];
                    float px = ing.position != null && ing.position.Length > 0 ? ing.position[0] : 0;
                    float py = ing.position != null && ing.position.Length > 1 ? ing.position[1] : 0;
                    float pz = ing.position != null && ing.position.Length > 2 ? ing.position[2] : 0.95f;
                    float rx = ing.rotation != null && ing.rotation.Length > 0 ? ing.rotation[0] : 0;
                    float ry = ing.rotation != null && ing.rotation.Length > 1 ? ing.rotation[1] : 0;
                    float rz = ing.rotation != null && ing.rotation.Length > 2 ? ing.rotation[2] : 0;
                    sb.AppendLine($"    {{\"IngredientID\":\"{ing.id}\",\"Rotation\":{{\"x\":{rx},\"y\":{ry},\"z\":{rz}}},\"Position\":{{\"x\":{px},\"y\":{py},\"z\":{pz}}},\"Size\":{SizeToInt(ing.size)}}}");
                    if (i < recipe.ingredients.Length - 1) sb.AppendLine(",");
                    else sb.AppendLine();
                }
            }
            sb.AppendLine("  ],");
            sb.AppendLine("  \"DoughPositions\": [{\"x\":0,\"y\":0,\"z\":0}],");
            sb.AppendLine("  \"ProfitFactor\": 1.5,");
            sb.AppendLine("  \"Owner\": null,");
            sb.AppendLine("  \"Texture\": \"\"");
            sb.AppendLine("}");
            File.WriteAllText(outputPath, sb.ToString());
            Debug.Log($"[JsonExporter] Wrote {outputPath}");
        }

        public static void WriteRecipe(RecipeData recipe, string outputPath)
        {
            // Strip _meta before writing (it's internal annotation)
            var meta = recipe._meta;
            recipe._meta = null;
            var json = JsonUtility.ToJson(recipe, true);
            recipe._meta = meta;
            File.WriteAllText(outputPath, json);
            Debug.Log($"[JsonExporter] Wrote recipe {outputPath}");
        }
    }
}
