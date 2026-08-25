using System.IO;
using UnityEngine;

namespace creator_ui.Recipe
{
    public static class IngredientCatalog
    {
        public static CatalogData Load()
        {
            var path = Path.Combine(Application.streamingAssetsPath, "catalog.json");
            if (!File.Exists(path))
                throw new FileNotFoundException(
                    $"catalog.json not found at {path}. Run 'pizza-agent extract-ingredients' first.");
            var json = File.ReadAllText(path);
            return JsonUtility.FromJson<CatalogData>(json);
        }

        public static IngredientData? GetIngredient(CatalogData catalog, string id)
        {
            if (catalog?.ingredients == null) return null;
            foreach (var ing in catalog.ingredients)
            {
                if (ing.id == id) return ing;
            }
            return null;
        }

        public static bool ContainsId(CatalogData catalog, string id)
        {
            return GetIngredient(catalog, id).HasValue;
        }
    }
}
