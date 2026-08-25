using creator_ui.LLM;
using System.Threading.Tasks;
using UnityEngine;

namespace creator_ui.Recipe
{
    public class RecipeComposer
    {
        private readonly LLMClient _client;

        public RecipeComposer(LLMClient client) { _client = client; }

        public async Task<RecipeData> ComposeAsync(string systemPrompt, string userPrompt)
        {
            var llmJson = await _client.CompleteAsync(systemPrompt, userPrompt);
            RecipeData recipe;
            try
            {
                recipe = JsonUtility.FromJson<RecipeData>(llmJson);
                if (recipe == null) throw new System.Exception("JsonUtility returned null");
            }
            catch (System.Exception ex)
            {
                Debug.LogError($"[RecipeComposer] LLM returned invalid JSON: {ex.Message}");
                throw;
            }

            var catalog = IngredientCatalog.Load();
            int unknownCount = 0;
            if (recipe.ingredients != null)
            {
                foreach (var ing in recipe.ingredients)
                {
                    if (!IngredientCatalog.ContainsId(catalog, ing.id))
                    {
                        Debug.LogWarning($"[RecipeComposer] Unknown ingredient '{ing.id}' - keeping but flagging");
                        unknownCount++;
                    }
                }
            }

            recipe.scores = ScoringEngine.Compute(recipe, catalog);
            recipe._meta = new MetaData { unknown_ingredient_count = unknownCount };
            return recipe;
        }
    }
}
