using NUnit.Framework;
using creator_ui.Recipe;
using Newtonsoft.Json.Linq;
using System.IO;

namespace creator_ui.tests.EditMode
{
    public class JsonExporterTests
    {
        [Test]
        public void WriteFinal_ProducesValidPC3DataContractShape()
        {
            var recipe = new JObject
            {
                ["name"] = "Test Pizza",
                ["dough"] = new JObject { ["size"] = "Large", ["shape"] = "Round" },
                ["ingredients"] = new JArray(
                    new JObject
                    {
                        ["id"] = "PizzaSauce",
                        ["amount_g"] = 100.0,
                        ["position"] = new JArray(0, 0, 0.95),
                        ["rotation"] = new JArray(0, 0, 0),
                        ["size"] = "Medium"
                    }
                )
            };
            var tmpPath = Path.GetTempFileName();
            try
            {
                JsonExporter.WriteFinal(recipe, tmpPath);
                var written = JObject.Parse(File.ReadAllText(tmpPath));
                Assert.IsNotNull(written["ID"]);
                Assert.IsNotNull(written["Ingredients"]);
                Assert.AreEqual("PizzaSauce", (string?)written["Ingredients"]![0]!["IngredientID"]);
                // PC3 IngredientSize: Medium=1
                Assert.AreEqual(1, (int?)written["Ingredients"]![0]!["Size"]);
            }
            finally { File.Delete(tmpPath); }
        }

        [Test]
        public void WriteFinal_SizeEnum_LargeMapsToZero()
        {
            var recipe = new JObject
            {
                ["ingredients"] = new JArray(
                    new JObject
                    {
                        ["id"] = "Mozzarella",
                        ["amount_g"] = 50.0,
                        ["position"] = new JArray(0, 0, 0.95),
                        ["rotation"] = new JArray(0, 0, 0),
                        ["size"] = "Large"
                    }
                )
            };
            var tmpPath = Path.GetTempFileName();
            try
            {
                JsonExporter.WriteFinal(recipe, tmpPath);
                var written = JObject.Parse(File.ReadAllText(tmpPath));
                Assert.AreEqual(0, (int?)written["Ingredients"]![0]!["Size"]);  // Large=0
            }
            finally { File.Delete(tmpPath); }
        }

        [Test]
        public void WriteFinal_SizeEnum_SmallMapsToTwo()
        {
            var recipe = new JObject
            {
                ["ingredients"] = new JArray(
                    new JObject
                    {
                        ["id"] = "Jalapeno",
                        ["amount_g"] = 25.0,
                        ["position"] = new JArray(0, 0, 0.95),
                        ["rotation"] = new JArray(0, 0, 0),
                        ["size"] = "Small"
                    }
                )
            };
            var tmpPath = Path.GetTempFileName();
            try
            {
                JsonExporter.WriteFinal(recipe, tmpPath);
                var written = JObject.Parse(File.ReadAllText(tmpPath));
                Assert.AreEqual(2, (int?)written["Ingredients"]![0]!["Size"]);  // Small=2
            }
            finally { File.Delete(tmpPath); }
        }

        [Test]
        public void WriteRecipe_StoresRecipeJson()
        {
            var recipe = new JObject { ["name"] = "Test", ["ingredients"] = new JArray() };
            var tmpPath = Path.GetTempFileName();
            try
            {
                JsonExporter.WriteRecipe(recipe, tmpPath);
                Assert.IsTrue(File.Exists(tmpPath));
                var written = JObject.Parse(File.ReadAllText(tmpPath));
                Assert.AreEqual("Test", (string?)written["name"]);
            }
            finally { File.Delete(tmpPath); }
        }
    }
}
