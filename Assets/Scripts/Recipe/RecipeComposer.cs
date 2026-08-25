using creator_ui.LLM;
using Newtonsoft.Json.Linq;
using System.Threading.Tasks;
using UnityEngine;

namespace creator_ui.Recipe
{
    public class RecipeComposer
    {
        private readonly LLMClient _client;

        public RecipeComposer(LLMClient client) { _client = client; }

        public async Task<JObject> ComposeAsync(string systemPrompt, string userPrompt)
        {
            var llmJson = await _client.CompleteAsync(systemPrompt, userPrompt);
            JObject recipe;
            try
            {
                recipe = JObject.Parse(llmJson);
            }
            catch (System.Exception ex)
            {
                Debug.LogError($"[RecipeComposer] LLM returned invalid JSON: {ex.Message}");
                throw;
            }

            var catalog = IngredientCatalog.Load();
            var ingredients = recipe["ingredients"] as JArray;
            int unknownCount = 0;
            if (ingredients != null)
            {
                foreach (var ing in ingredients)
                {
                    var id = (string?)ing["id"];
                    if (!IngredientCatalog.ContainsId(catalog, id!))
                    {
                        Debug.LogWarning($"[RecipeComposer] Unknown ingredient '{id}' - keeping but flagging");
                        unknownCount++;
                    }
                }
            }

            recipe["scores"] = ScoringEngine.Compute(recipe, catalog);
            recipe["_meta"] = new JObject
            {
                ["unknown_ingredient_count"] = unknownCount
            };
            return recipe;
        }
    }
}
