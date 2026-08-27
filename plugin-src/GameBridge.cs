using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using Service.Database;
using Service.PizzaCreator;
using Service.Serializer;
using UnityEngine;
using UserInterface;
using Zenject;

namespace Barros.PizzaCreator.AI
{
    public sealed class GameBridge
    {
        private IPizzaCreatorService pizzaCreator;
        private IDatabaseService database;
        private ISerializerService serializer;
        private PizzaModel restorePoint;
        private PizzaModel savedPoint;
        private AiRecipe lastRecipe;
        private PizzaModel lastCandidate;
        private string savedRecipePath;
        private string lastExportPath;
        private readonly EvidenceRecorder evidence;

        public bool Ready { get { return pizzaCreator != null && database != null && serializer != null; } }
        public string SavedRecipePath { get { return savedRecipePath; } }
        public string LastExportPath { get { return lastExportPath; } }

        public GameBridge(EvidenceRecorder recorder)
        {
            evidence = recorder;
        }

        [Inject]
        private void Initialize(IPizzaCreatorService pizzaCreatorService, IDatabaseService databaseService, ISerializerService serializerService)
        {
            pizzaCreator = pizzaCreatorService;
            database = databaseService;
            serializer = serializerService;
        }

        public List<AiCatalogIngredient> BuildCatalog()
        {
            List<AiCatalogIngredient> output = new List<AiCatalogIngredient>();
            if (!Ready) return output;
            List<IngredientModel> medium = database.GetAllIngredients(IngredientModel.IngredientSize.Medium);
            for (int i = 0; i < medium.Count; i++)
            {
                IngredientModel source = medium[i];
                AiCatalogIngredient record = new AiCatalogIngredient();
                record.Id = source.ID;
                record.Name = string.IsNullOrEmpty(source.Name) ? source.ID : source.Name;
                record.TypeId = source.TypeID;
                record.Craziness = source.Craziness;
                AddSize(record, source.ID, IngredientModel.IngredientSize.Large);
                AddSize(record, source.ID, IngredientModel.IngredientSize.Medium);
                AddSize(record, source.ID, IngredientModel.IngredientSize.Small);
                output.Add(record);
            }
            return output;
        }

        private void AddSize(AiCatalogIngredient record, string id, IngredientModel.IngredientSize size)
        {
            IngredientModel model = database.GetIngredientByID(id, size);
            if (model == null) return;
            AiCatalogSize item = new AiCatalogSize();
            item.Size = size.ToString();
            item.Grams = model.Amount;
            item.Cost = model.Price;
            record.Sizes.Add(item);
        }

        public string DescribeCurrentPizza()
        {
            if (!Ready) return "Game services are not ready.";
            PizzaModel current = pizzaCreator.GetCurrentPizza();
            if (current == null) return "No pizza is currently loaded.";
            Dictionary<string, int> counts = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
            for (int i = 0; i < current.ingredients.Count; i++)
            {
                PizzaModel.IngredientContainerModel placed = current.ingredients[i];
                if (placed == null || placed.Ingredient == null) continue;
                string id = placed.Ingredient.ID;
                if (!counts.ContainsKey(id)) counts[id] = 0;
                counts[id]++;
            }
            StringBuilder text = new StringBuilder();
            text.Append("Current pizza '").Append(current.ID).Append("'; cost ")
                .Append(current.Cost.ToString("0.00")).Append("; price ")
                .Append(current.Price.ToString("0.00")).Append("; ingredients: ");
            bool first = true;
            foreach (KeyValuePair<string, int> entry in counts)
            {
                if (!first) text.Append(", ");
                text.Append(entry.Key).Append(" x").Append(entry.Value);
                first = false;
            }
            if (counts.Count == 0) text.Append("none yet");
            return text.ToString();
        }

        public AiRecipe Prepare(AiRecipe recipe)
        {
            if (!Ready) throw new InvalidOperationException("Pizza Creator services are not ready.");
            if (recipe == null) throw new ArgumentNullException("recipe");
            PizzaModel candidate = BuildModel(recipe);
            ScoreWithGame(candidate, recipe);
            lastRecipe = recipe;
            lastCandidate = candidate;
            return recipe;
        }

        public void Preview(AiRecipe recipe)
        {
            if (!Ready) throw new InvalidOperationException("Pizza Creator services are not ready.");
            CaptureRestorePoint();
            if (recipe != lastRecipe || lastCandidate == null) Prepare(recipe);
            pizzaCreator.LoadPizzaFromModel(lastCandidate);
            evidence.Record("action.preview.success", DescribeCandidate(lastCandidate));
        }

        public void Apply(AiRecipe recipe)
        {
            if (!Ready) throw new InvalidOperationException("Pizza Creator services are not ready.");
            if (recipe != lastRecipe || lastCandidate == null) Prepare(recipe);
            pizzaCreator.LoadPizzaFromModel(lastCandidate);
            restorePoint = null;
            evidence.Record("action.apply.success", DescribeCandidate(lastCandidate));
        }

        public bool Restore()
        {
            if (!Ready || restorePoint == null) return false;
            pizzaCreator.LoadPizzaFromModel(restorePoint);
            restorePoint = null;
            evidence.Record("action.restore.success", "Captured pre-preview PizzaModel reloaded.");
            return true;
        }

        public void SaveCurrentToRecipeBook()
        {
            if (!Ready) throw new InvalidOperationException("Pizza Creator services are not ready.");
            PizzaModel current = pizzaCreator.GetCurrentPizza();
            if (current == null) throw new InvalidOperationException("No current pizza is available to save.");
            pizzaCreator.SaveCurrentPizzaToRecipes();
            List<PizzaModel> recipes = pizzaCreator.GetAllRecipes();
            PizzaModel persisted = null;
            if (recipes != null)
                for (int i = 0; i < recipes.Count; i++)
                    if (recipes[i] != null && string.Equals(recipes[i].ID, current.ID, StringComparison.Ordinal)) persisted = recipes[i];
            if (persisted == null) throw new InvalidOperationException("Native save returned, but the recipe was not found in GetAllRecipes().");

            savedRecipePath = Path.Combine(Paths.recipes, current.ID + ".json");
            if (!File.Exists(savedRecipePath))
                throw new InvalidOperationException("Native recipe list updated, but the expected persisted JSON is missing: " + savedRecipePath);
            FileInfo persistedFile = new FileInfo(savedRecipePath);
            if (persistedFile.Length <= 2)
                throw new InvalidOperationException("Native recipe JSON is empty: " + savedRecipePath);

            // Copy the model returned by the native recipe service, not the transient
            // current model. SaveToRecipes refreshes dough coordinates from the live
            // PizzaDoughPart objects before writing the JSON.
            savedPoint = new PizzaModel();
            savedPoint.Bind();
            savedPoint.CopyValues(persisted);
            evidence.Record("action.save.success", DescribeCandidate(savedPoint) + "; json_bytes=" + persistedFile.Length + "; json_path=" + savedRecipePath);
        }

        public bool ReloadLastSaved(out string detail)
        {
            if (!Ready) { detail = "Pizza Creator services are not ready."; return false; }
            if (string.IsNullOrEmpty(savedRecipePath) || !File.Exists(savedRecipePath))
            {
                detail = "Save a recipe with the AI panel before pressing F9.";
                return false;
            }

            string json = File.ReadAllText(savedRecipePath);
            PizzaModel fromDisk = serializer.DeserializeToObject<PizzaModel>(json);
            if (fromDisk == null) throw new InvalidOperationException("The native serializer returned no PizzaModel for " + savedRecipePath);
            for (int i = 0; i < fromDisk.ingredients.Count; i++)
            {
                PizzaModel.IngredientContainerModel placed = fromDisk.ingredients[i];
                if (placed == null) throw new InvalidOperationException("The persisted recipe contains a null ingredient placement.");
                placed.Bind();
            }
            fromDisk.Bind();
            for (int i = 0; i < fromDisk.ingredients.Count; i++)
            {
                PizzaModel.IngredientContainerModel placed = fromDisk.ingredients[i];
                placed.Ingredient = database.GetIngredientByID(placed.IngredientID, placed.Size);
                if (placed.Ingredient == null)
                    throw new InvalidOperationException("The persisted recipe references an unknown ingredient: " + placed.IngredientID + " / " + placed.Size);
            }

            savedPoint = fromDisk;
            pizzaCreator.LoadPizzaFromModel(fromDisk);
            detail = "PC3 serializer disk reload requested for '" + fromDisk.ID + "'.";
            evidence.Record("action.reload.requested", DescribeCandidate(fromDisk) + "; json_path=" + savedRecipePath);
            return true;
        }

        public string ExportCurrentJpeg()
        {
            if (!Ready) throw new InvalidOperationException("Pizza Creator services are not ready.");
            PizzaModel current = pizzaCreator.GetCurrentPizza();
            if (current == null) throw new InvalidOperationException("No current pizza is available to export.");
            ScreenshotButton[] allButtons = UnityEngine.Resources.FindObjectsOfTypeAll<ScreenshotButton>();
            ScreenshotButton stockButton = null;
            int sceneButtons = 0;
            for (int i = 0; i < allButtons.Length; i++)
            {
                ScreenshotButton candidate = allButtons[i];
                if (candidate == null || !candidate.gameObject.scene.IsValid()) continue;
                sceneButtons++;
                stockButton = candidate;
            }
            if (sceneButtons != 1 || stockButton == null)
                throw new InvalidOperationException("Expected one scene-local stock ScreenshotButton, but found " + sceneButtons + ". Export stopped to avoid choosing the wrong camera or UI.");
            if (stockButton.screenCapture == null || stockButton.specialScreenshotUI == null)
                throw new InvalidOperationException("The stock ScreenshotButton is missing its capture camera or screenshot-only UI reference.");

            string fileName = MakeSafeName(current.ID);
            bool previousScreenshotUiState = stockButton.specialScreenshotUI.activeSelf;
            CaptureUtility.Data data;
            try
            {
                stockButton.specialScreenshotUI.SetActive(true);
                data = stockButton.screenCapture.Capture(fileName);
            }
            finally
            {
                stockButton.specialScreenshotUI.SetActive(previousScreenshotUiState);
            }
            if (data == null || string.IsNullOrEmpty(data.combinedPath) || !File.Exists(data.combinedPath))
                throw new InvalidOperationException("The stock JPG capture returned without a persisted output file.");
            if (data.bytes == null || data.bytes.Length < 4 || data.bytes[0] != 0xFF || data.bytes[1] != 0xD8 ||
                data.bytes[data.bytes.Length - 2] != 0xFF || data.bytes[data.bytes.Length - 1] != 0xD9)
                throw new InvalidOperationException("The stock capture output is not a complete JPEG byte stream.");

            lastExportPath = data.combinedPath;
            string dimensions = data.texture == null ? "unknown" : data.texture.width + "x" + data.texture.height;
            evidence.Record("action.export_jpg.success", "path=" + lastExportPath + "; bytes=" + data.bytes.Length + "; dimensions=" + dimensions + "; quality=" + stockButton.screenCapture.defaultJPGQuality + "; screenshot_ui_restored=" + (stockButton.specialScreenshotUI.activeSelf == previousScreenshotUiState));
            return lastExportPath;
        }

        public bool VerifyLastSavedReload(out string detail)
        {
            if (!Ready) { detail = "Pizza Creator services are not ready."; return false; }
            if (savedPoint == null) { detail = "Save a recipe with the AI panel before pressing F9."; return false; }
            PizzaModel current = pizzaCreator.GetCurrentPizza();
            if (current == null) { detail = "No pizza is currently loaded."; return false; }
            string expected = ModelSignature(savedPoint);
            string actual = ModelSignature(current);
            bool match = string.Equals(expected, actual, StringComparison.Ordinal);
            detail = match
                ? "Reloaded pizza matches saved name, profit factor, dough positions, ingredient IDs, sizes, positions and rotations."
                : "Reload mismatch. Expected " + ShortHash(expected) + " but observed " + ShortHash(actual) + ".";
            return match;
        }

        private void CaptureRestorePoint()
        {
            if (restorePoint != null) return;
            PizzaModel current = pizzaCreator.GetCurrentPizza();
            if (current == null) return;
            restorePoint = new PizzaModel();
            restorePoint.Bind();
            restorePoint.CopyValues(current);
        }

        private static string DescribeCandidate(PizzaModel model)
        {
            if (model == null) return "null PizzaModel";
            return "id=" + model.ID + "; placements=" + model.ingredients.Count + "; dough=" + model.doughPositions.Count + "; profit_factor=" + model.ProfitFactor.ToString("0.000");
        }

        private static string ModelSignature(PizzaModel model)
        {
            if (model == null) return "null";
            StringBuilder value = new StringBuilder();
            value.Append(model.ID).Append('|').Append(model.ProfitFactor.ToString("R"));
            value.Append("|d:").Append(model.doughPositions.Count);
            for (int i = 0; i < model.doughPositions.Count; i++) AppendVector(value, model.doughPositions[i]);
            value.Append("|i:").Append(model.ingredients.Count);
            for (int i = 0; i < model.ingredients.Count; i++)
            {
                PizzaModel.IngredientContainerModel item = model.ingredients[i];
                if (item == null) { value.Append("|null"); continue; }
                string id = item.Ingredient != null ? item.Ingredient.ID : item.IngredientID;
                value.Append('|').Append(id).Append(':').Append((int)item.Size);
                AppendVector(value, item.Position);
                AppendVector(value, item.Rotation);
            }
            return value.ToString();
        }

        private static void AppendVector(StringBuilder value, Vector3 vector)
        {
            value.Append(':').Append(vector.x.ToString("R")).Append(',').Append(vector.y.ToString("R")).Append(',').Append(vector.z.ToString("R"));
        }

        private static string ShortHash(string value)
        {
            unchecked
            {
                uint hash = 2166136261;
                for (int i = 0; i < value.Length; i++) hash = (hash ^ value[i]) * 16777619;
                return hash.ToString("X8");
            }
        }

        private PizzaModel BuildModel(AiRecipe recipe)
        {
            PizzaModel model = new PizzaModel();
            model.Bind();
            model.ID = MakeSafeName(recipe.Name);
            model.ProfitFactor = Mathf.Clamp(recipe.ProfitFactor, 0f, 2f);
            PizzaShapeData shape = database.GetPizzaShape(NormalizeShape(recipe.Shape));
            if (shape == null) shape = database.GetPizzaShape("Round");
            if (shape != null && shape.DoughPositions != null)
                model.doughPositions.AddRange(shape.DoughPositions);

            System.Random random = new System.Random(recipe.Seed == 0 ? StableSeed(recipe.Name) : recipe.Seed);
            int globalIndex = 0;
            const int maximumPlacements = 180;
            for (int ingredientIndex = 0; ingredientIndex < recipe.Ingredients.Count; ingredientIndex++)
            {
                AiRecipeIngredient request = recipe.Ingredients[ingredientIndex];
                IngredientModel.IngredientSize size = ParseSize(request.Size);
                IngredientModel ingredient = database.GetIngredientByID(request.Id, size);
                if (ingredient == null || ingredient.Amount <= 0f) continue;
                int count = Mathf.Clamp(Mathf.RoundToInt(request.TargetGrams / ingredient.Amount), 1, 40);
                for (int piece = 0; piece < count && globalIndex < maximumPlacements; piece++)
                {
                    PizzaModel.IngredientContainerModel placed = new PizzaModel.IngredientContainerModel();
                    placed.Bind();
                    placed.Ingredient = ingredient;
                    placed.Position = PositionFor(request.Distribution, piece, count, globalIndex, random, recipe.Shape);
                    placed.Rotation = new Vector3(0f, (float)(random.NextDouble() * 360.0), 0f);
                    model.ingredients.Add(placed);
                    globalIndex++;
                }
            }
            model.CalculateCosts();
            return model;
        }

        private static string MakeSafeName(string value)
        {
            string name = string.IsNullOrEmpty(value) ? "Barro's AI Pizza" : value.Trim();
            char[] invalid = Path.GetInvalidFileNameChars();
            StringBuilder safe = new StringBuilder(name.Length);
            for (int i = 0; i < name.Length; i++)
                if (Array.IndexOf(invalid, name[i]) < 0) safe.Append(name[i]);
            name = safe.ToString().Trim().TrimEnd('.');
            if (string.IsNullOrEmpty(name)) name = "Barro's AI Pizza";
            if (name.Length > 54) name = name.Substring(0, 54);
            return name;
        }

        private static string NormalizeShape(string value)
        {
            string[] shapes = { "Round", "Square", "Star", "Triangle" };
            for (int i = 0; i < shapes.Length; i++)
                if (string.Equals(shapes[i], value, StringComparison.OrdinalIgnoreCase)) return shapes[i];
            return "Round";
        }

        private static IngredientModel.IngredientSize ParseSize(string value)
        {
            IngredientModel.IngredientSize parsed;
            if (Enum.TryParse<IngredientModel.IngredientSize>(value, true, out parsed)) return parsed;
            return IngredientModel.IngredientSize.Medium;
        }

        private static int StableSeed(string value)
        {
            unchecked
            {
                int hash = 17;
                string text = value ?? "AI Pizza";
                for (int i = 0; i < text.Length; i++) hash = hash * 31 + text[i];
                return hash & 0x7fffffff;
            }
        }

        private static Vector3 PositionFor(string distribution, int index, int count, int global, System.Random random, string shape)
        {
            string mode = (distribution ?? "even").ToLowerInvariant();
            double angle = (index * 2.399963229728653 + random.NextDouble() * 0.35);
            double radius;
            if (mode == "center") radius = Math.Sqrt(random.NextDouble()) * 1.15;
            else if (mode == "ring") radius = 1.35 + random.NextDouble() * 0.55;
            else if (mode == "edge") radius = 1.9 + random.NextDouble() * 0.25;
            else if (mode == "spiral") radius = 0.35 + 1.75 * ((index + 1.0) / Math.Max(1.0, count));
            else if (mode == "artistic") radius = 0.65 + 1.25 * Math.Abs(Math.Sin(angle * 2.5));
            else radius = Math.Sqrt(random.NextDouble()) * 2.08;
            float localX = (float)(Math.Cos(angle) * radius);
            float localZ = (float)(Math.Sin(angle) * radius);
            if (string.Equals(shape, "Square", StringComparison.OrdinalIgnoreCase))
            {
                localX = Mathf.Clamp(localX * 1.08f, -2.15f, 2.15f);
                localZ = Mathf.Clamp(localZ * 1.08f, -2.15f, 2.15f);
            }
            return new Vector3(-3f + localX, 1f + global * 0.01f, localZ);
        }

        private void ScoreWithGame(PizzaModel model, AiRecipe recipe)
        {
            if (recipe.Scores == null) recipe.Scores = new AiRecipeScores();
            List<CitizenTypeController> controllers = database.GetAllCitizenTypeControllers();
            float recipeTaste = 0f;
            float overall = 0f;
            float priceTaste = 0f;
            int valid = 0;
            if (controllers != null)
            {
                for (int i = 0; i < controllers.Count; i++)
                {
                    try
                    {
                        recipeTaste += controllers[i].RatePizzaRecipe(model);
                        overall += controllers[i].RatePizzaOverallTaste(model);
                        priceTaste += controllers[i].RatePizzaPriceTaste(model) / 100f;
                        valid++;
                    }
                    catch { }
                }
            }
            if (valid > 0)
            {
                recipe.Scores.Taste = Mathf.Clamp01(recipeTaste / valid) * 100f;
                recipe.Scores.Popularity = Mathf.Clamp01(overall / valid) * 100f;
            }
            recipe.Scores.Cost = model.Cost;
            recipe.Scores.Profit = model.Price > 0f ? ((model.Price - model.Cost) / model.Price) * 100f : 0f;
            float placementVariety = 0f;
            HashSet<string> distributions = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            float craziness = 0f;
            for (int i = 0; i < recipe.Ingredients.Count; i++)
            {
                distributions.Add(recipe.Ingredients[i].Distribution ?? "even");
                IngredientModel item = database.GetIngredientByID(recipe.Ingredients[i].Id, ParseSize(recipe.Ingredients[i].Size));
                if (item != null) craziness += item.Craziness;
            }
            placementVariety = distributions.Count * 7f;
            float averageCrazy = recipe.Ingredients.Count > 0 ? craziness / recipe.Ingredients.Count : 0f;
            recipe.Scores.Novelty = Mathf.Clamp(45f + averageCrazy * 35f + recipe.Ingredients.Count * 3f, 0f, 100f);
            recipe.Scores.Originality = Mathf.Clamp(48f + averageCrazy * 30f + placementVariety, 0f, 100f);
            recipe.Scores.Source = "Pizza Connection 3 native citizen ratings + deterministic novelty/originality";
        }
    }
}
