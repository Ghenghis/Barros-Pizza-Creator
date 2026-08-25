using Newtonsoft.Json.Linq;

namespace creator_ui.Recipe
{
    public static class ScoringEngine
    {
        public static JObject Compute(JObject recipe, JObject catalog)
        {
            var ingredients = recipe["ingredients"]!;
            double totalAmount = 0;
            double weightedTaste = 0;
            double totalCost = 0;
            foreach (var ing in ingredients)
            {
                var id = (string?)ing["id"];
                var amount = (double?)ing["amount_g"] ?? 0;
                var cat = IngredientCatalog.GetIngredient(catalog, id!);
                if (cat == null) continue;
                var taste = (double?)cat["taste_rating"] ?? 0;
                var basePrice = (double?)cat["base_price"] ?? 0;
                weightedTaste += taste * amount;
                totalAmount += amount;
                // PC3 formula: Price = Amount / 100 * BasePrice (IngredientModel.cs:402)
                totalCost += (amount / 100.0) * basePrice;
            }
            var tasteScore = totalAmount > 0 ? weightedTaste / totalAmount : 0;
            // Profit: assumed suggested = cost * 1.5
            return new JObject
            {
                ["taste"] = System.Math.Round(tasteScore, 1),
                ["cost_dollars"] = System.Math.Round(totalCost, 2),
                ["profit_percent"] = 50.0,
                ["novelty"] = 75.0
            };
        }
    }
}
