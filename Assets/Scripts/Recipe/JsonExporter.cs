using Newtonsoft.Json.Linq;
using System;
using System.IO;
using UnityEngine;

namespace creator_ui.Recipe
{
    public static class JsonExporter
    {
        // PC3 IngredientSize enum: Large=0, Medium=1, Small=2 (IngredientModel.cs:12-17)
        private static int SizeToInt(string size) => size switch
        {
            "Large" => 0,
            "Medium" => 1,
            "Small" => 2,
            _ => 1
        };

        public static void WriteFinal(JObject recipe, string outputPath)
        {
            var ingredients = new JArray();
            foreach (var ing in recipe["ingredients"]!)
            {
                var pos = (JArray)ing["position"]!;
                var rot = (JArray)ing["rotation"]!;
                ingredients.Add(new JObject
                {
                    ["IngredientID"] = (string?)ing["id"],
                    ["Rotation"] = new JObject { ["x"] = rot[0], ["y"] = rot[1], ["z"] = rot[2] },
                    ["Position"] = new JObject { ["x"] = pos[0], ["y"] = pos[1], ["z"] = pos[2] },
                    ["Size"] = SizeToInt((string?)ing["size"] ?? "Medium")
                });
            }

            var final = new JObject
            {
                ["ID"] = Guid.NewGuid().ToString(),
                ["Ingredients"] = ingredients,
                ["DoughPositions"] = new JArray(new JObject { ["x"] = 0, ["y"] = 0, ["z"] = 0 }),
                ["ProfitFactor"] = 1.5,
                ["Owner"] = null,
                ["Texture"] = ""
            };
            File.WriteAllText(outputPath, final.ToString(Newtonsoft.Json.Formatting.Indented));
            Debug.Log($"[JsonExporter] Wrote {outputPath}");
        }

        public static void WriteRecipe(JObject recipe, string outputPath)
        {
            File.WriteAllText(outputPath, recipe.ToString(Newtonsoft.Json.Formatting.Indented));
            Debug.Log($"[JsonExporter] Wrote recipe {outputPath}");
        }
    }
}
