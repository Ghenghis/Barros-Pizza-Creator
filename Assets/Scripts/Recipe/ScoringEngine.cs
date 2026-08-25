using UnityEngine;

namespace creator_ui.Recipe
{
    public static class ScoringEngine
    {
        public static ScoresData Compute(RecipeData recipe, CatalogData catalog)
        {
            var scores = new ScoresData();
            if (recipe?.ingredients == null) return scores;
            float totalAmount = 0;
            float weightedTaste = 0;
            float totalCost = 0;
            foreach (var ing in recipe.ingredients)
            {
                var cat = IngredientCatalog.GetIngredient(catalog, ing.id);
                if (!cat.HasValue) continue;
                var ingredient = cat.Value;
                float amount = ing.amount_g;
                float taste = ingredient.taste_rating;
                float basePrice = ingredient.base_price;
                weightedTaste += taste * amount;
                totalAmount += amount;
                // PC3 formula: Price = Amount / 100 * BasePrice (IngredientModel.cs:402)
                totalCost += (amount / 100f) * basePrice;
            }
            scores.taste = totalAmount > 0 ? Mathf.Round(weightedTaste / totalAmount * 10f) / 10f : 0;
            scores.cost_dollars = Mathf.Round(totalCost * 100f) / 100f;
            scores.profit_percent = 50f;
            scores.novelty = 75f;
            return scores;
        }
    }
}
