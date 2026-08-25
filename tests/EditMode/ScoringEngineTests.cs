using NUnit.Framework;
using creator_ui.Recipe;
using Newtonsoft.Json.Linq;

namespace creator_ui.tests.EditMode
{
    public class ScoringEngineTests
    {
        [Test]
        public void Taste_WeightedAverage_ReturnsCorrectValue()
        {
            var recipe = new JObject
            {
                ["ingredients"] = new JArray(
                    new JObject { ["id"] = "PizzaSauce", ["amount_g"] = 100.0 },
                    new JObject { ["id"] = "Mozzarella", ["amount_g"] = 50.0 }
                )
            };
            var catalog = new JObject
            {
                ["ingredients"] = new JArray(
                    new JObject { ["id"] = "PizzaSauce", ["taste_rating"] = 60, ["base_price"] = 0.12 },
                    new JObject { ["id"] = "Mozzarella", ["taste_rating"] = 80, ["base_price"] = 0.15 }
                )
            };
            var scores = ScoringEngine.Compute(recipe, catalog);
            // weighted avg: (60*100 + 80*50) / 150 = 66.67
            Assert.That(scores["taste"].Value<double>(), Is.EqualTo(66.67).Within(0.1));
        }

        [Test]
        public void Cost_PC3Formula_MatchesIngredientModelLine402()
        {
            var recipe = new JObject
            {
                ["ingredients"] = new JArray(
                    new JObject { ["id"] = "PizzaSauce", ["amount_g"] = 100.0 }
                )
            };
            var catalog = new JObject
            {
                ["ingredients"] = new JArray(
                    new JObject { ["id"] = "PizzaSauce", ["taste_rating"] = 60, ["base_price"] = 0.12 }
                )
            };
            var scores = ScoringEngine.Compute(recipe, catalog);
            // PC3: Price = Amount / 100 * BasePrice = 100/100 * 0.12 = 0.12
            Assert.That(scores["cost_dollars"].Value<double>(), Is.EqualTo(0.12).Within(0.001));
        }

        [Test]
        public void Cost_UnknownIngredient_Skipped()
        {
            var recipe = new JObject
            {
                ["ingredients"] = new JArray(
                    new JObject { ["id"] = "UnknownIngredient", ["amount_g"] = 100.0 }
                )
            };
            var catalog = new JObject { ["ingredients"] = new JArray() };
            var scores = ScoringEngine.Compute(recipe, catalog);
            Assert.That(scores["cost_dollars"].Value<double>(), Is.EqualTo(0).Within(0.001));
        }
    }
}
