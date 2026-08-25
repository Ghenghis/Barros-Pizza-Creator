using Newtonsoft.Json.Linq;
using System.IO;
using UnityEngine;

namespace creator_ui.Recipe
{
    public static class IngredientCatalog
    {
        public static JObject Load()
        {
            var path = Path.Combine(Application.streamingAssetsPath, "catalog.json");
            if (!File.Exists(path))
                throw new FileNotFoundException(
                    $"catalog.json not found at {path}. Run 'pizza-agent extract-ingredients' first.");
            return JObject.Parse(File.ReadAllText(path));
        }

        public static JObject? GetIngredient(JObject catalog, string id)
        {
            foreach (var ing in catalog["ingredients"]!)
            {
                if ((string?)ing["id"] == id) return (JObject)ing;
            }
            return null;
        }

        public static bool ContainsId(JObject catalog, string id)
        {
            return GetIngredient(catalog, id) != null;
        }
    }
}
