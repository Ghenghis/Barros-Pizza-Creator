using System;
using System.Collections.Generic;
using System.Reflection;
using System.Text;
using Service.Audio;
using Service.Database;
using Service.PizzaCreator;
using UnityEngine;
using Zenject;

namespace Barros.PizzaCreator.AI
{
    public sealed class GameBridge
    {
        private IPizzaCreatorService pizzaCreator;
        private IDatabaseService database;
        private IAudioService audio;
        private PizzaModel restorePoint;
        private PizzaModel savedPoint;
        private AiRecipe lastRecipe;
        private PizzaModel lastCandidate;
        private readonly EvidenceRecorder evidence;

        public bool Ready { get { return pizzaCreator != null && database != null && audio != null; } }

        public GameBridge(EvidenceRecorder recorder)
        {
            evidence = recorder;
        }

        [Inject]
        private void Initialize(IPizzaCreatorService pizzaCreatorService, IDatabaseService databaseService, IAudioService audioService)
        {
            pizzaCreator = pizzaCreatorService;
            database = databaseService;
            audio = audioService;
        }

        public AudioSource GetMusicSource()
        {
            if (audio == null) return null;
            try
            {
                FieldInfo field = audio.GetType().GetField("musicSource", BindingFlags.Instance | BindingFlags.NonPublic);
                return field == null ? null : field.GetValue(audio) as AudioSource;
            }
            catch { return null; }
        }

        public void StartBarrosMusic(AudioClip clip, float volume)
        {
            if (audio == null || clip == null) return;
            audio.StartMusic(clip, 0.25f, 1f, Mathf.Clamp01(volume), false);
            evidence.Record("media.stock_replaced", "track=" + clip.name);
        }

        public void PlayStockCreatorMusic()
        {
            if (audio == null) return;
            audio.StartPreloadedMusic("PizzaCreator\\PizzaCreator", 0.25f, 1f, 1f, true);
            evidence.Record("media.stock_restored", "PizzaCreator\\PizzaCreator");
        }

        public void PauseMusic() { if (audio != null) audio.PauseMusic(); }
        public void ResumeMusic() { if (audio != null) audio.ResumeMusic(); }
        public void StopMusic() { if (audio != null) audio.StopMusic(0f); }
        public void SetMusicVolume(float volume) { if (audio != null) audio.SetMusicVolume(Mathf.Clamp01(volume)); }

        public void SetMusicTone(float bassDb, float midDb, float trebleDb)
        {
            if (audio == null) return;
            // Use the game's native mixer effects rather than an audio-thread
            // callback in the mod. Cutoffs handle low/high cuts and the strongest
            // requested band receives the parametric focus.
            float highpass = bassDb < 0f ? Mathf.Lerp(10f, 760f, -bassDb / 12f) : 10f;
            float lowpass = trebleDb < 0f ? Mathf.Lerp(22000f, 3200f, -trebleDb / 12f) : 22000f;
            audio.SetMusicHighpass(highpass);
            audio.SetMusicLowpass(lowpass);
            float dominant = bassDb;
            float frequency = 125f;
            float octave = 1.35f;
            if (Mathf.Abs(midDb) > Mathf.Abs(dominant)) { dominant = midDb; frequency = 1000f; octave = 2f; }
            if (Mathf.Abs(trebleDb) > Mathf.Abs(dominant)) { dominant = trebleDb; frequency = 7500f; octave = 1.35f; }
            audio.SetMusicParamEQ(frequency, octave, Mathf.Pow(10f, Mathf.Clamp(dominant, -12f, 12f) / 20f));
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
            evidence.Record("action.preview.success", DescribeCandidate(lastCandidate) + DescribeArtwork(recipe));
        }

        public void Apply(AiRecipe recipe)
        {
            if (!Ready) throw new InvalidOperationException("Pizza Creator services are not ready.");
            if (recipe != lastRecipe || lastCandidate == null) Prepare(recipe);
            pizzaCreator.LoadPizzaFromModel(lastCandidate);
            restorePoint = null;
            evidence.Record("action.apply.success", DescribeCandidate(lastCandidate) + DescribeArtwork(recipe));
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
            savedPoint = new PizzaModel();
            savedPoint.Bind();
            savedPoint.CopyValues(current);
            List<PizzaModel> recipes = pizzaCreator.GetAllRecipes();
            bool present = false;
            if (recipes != null)
                for (int i = 0; i < recipes.Count; i++)
                    if (recipes[i] != null && string.Equals(recipes[i].ID, current.ID, StringComparison.Ordinal)) present = true;
            if (!present) throw new InvalidOperationException("Native save returned, but the recipe was not found in GetAllRecipes().");
            evidence.Record("action.save.success", DescribeCandidate(savedPoint));
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

        private static string DescribeArtwork(AiRecipe recipe)
        {
            if (recipe == null || recipe.Artwork == null || !recipe.Artwork.Enabled) return "";
            return "; artwork=" + recipe.Artwork.Template + "; subject=" + recipe.Artwork.Subject
                + "; detail=" + recipe.Artwork.Detail + "; planned=" + recipe.Artwork.PieceCount
                + "; algorithm=" + recipe.Artwork.Algorithm;
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
            if (recipe.Placements != null && recipe.Placements.Count > 0)
            {
                List<AiArtworkPlacement> planned = new List<AiArtworkPlacement>(recipe.Placements);
                planned.Sort(delegate(AiArtworkPlacement left, AiArtworkPlacement right)
                {
                    int layer = left.Layer.CompareTo(right.Layer);
                    if (layer != 0) return layer;
                    int vertical = left.Y.CompareTo(right.Y);
                    return vertical != 0 ? vertical : left.X.CompareTo(right.X);
                });
                for (int index = 0; index < planned.Count && globalIndex < maximumPlacements; index++)
                {
                    AiArtworkPlacement request = planned[index];
                    IngredientModel.IngredientSize size = ParseSize(request.Size);
                    IngredientModel ingredient = database.GetIngredientByID(request.IngredientId, size);
                    if (ingredient == null || ingredient.Amount <= 0f) continue;
                    PizzaModel.IngredientContainerModel placed = new PizzaModel.IngredientContainerModel();
                    placed.Bind();
                    placed.Ingredient = ingredient;
                    placed.Position = PositionForArtwork(request, globalIndex, recipe.Shape);
                    placed.Rotation = new Vector3(0f, Mathf.Repeat(request.Rotation, 360f), 0f);
                    model.ingredients.Add(placed);
                    globalIndex++;
                }
            }
            else
            {
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
            }
            model.CalculateCosts();
            return model;
        }

        private static string MakeSafeName(string value)
        {
            string name = string.IsNullOrEmpty(value) ? "Barro's AI Pizza" : value.Trim();
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
            // Use the pizza-wide placement index so every ingredient family
            // continues the same golden-angle spread. Restarting from the
            // per-ingredient index clustered each new topping on one side.
            double angle = (global * 2.399963229728653 + random.NextDouble() * 0.35);
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

        private static Vector3 PositionForArtwork(AiArtworkPlacement placement, int global, string shape)
        {
            float normalizedX = Mathf.Clamp(placement.X, -0.92f, 0.92f);
            float normalizedZ = Mathf.Clamp(placement.Y, -0.92f, 0.92f);
            float radius = Mathf.Sqrt(normalizedX * normalizedX + normalizedZ * normalizedZ);
            if (string.Equals(shape, "Triangle", StringComparison.OrdinalIgnoreCase))
            {
                float halfWidth = Mathf.Max(0.08f, (0.94f - normalizedZ) * 0.53f);
                normalizedX = Mathf.Clamp(normalizedX, -halfWidth, halfWidth);
                normalizedZ = Mathf.Clamp(normalizedZ, -0.84f, 0.86f);
            }
            else if (string.Equals(shape, "Star", StringComparison.OrdinalIgnoreCase) && radius > 0.001f)
            {
                float angle = Mathf.Atan2(normalizedZ, normalizedX);
                float starLimit = 0.54f + 0.34f * (0.5f + 0.5f * Mathf.Cos(angle * 5f));
                if (radius > starLimit)
                {
                    float scale = starLimit / radius;
                    normalizedX *= scale;
                    normalizedZ *= scale;
                }
            }
            else if (!string.Equals(shape, "Square", StringComparison.OrdinalIgnoreCase) && radius > 0.92f)
            {
                float scale = 0.92f / radius;
                normalizedX *= scale;
                normalizedZ *= scale;
            }
            float localX = normalizedX * 2.22f;
            float localZ = normalizedZ * 2.22f;
            float localY = 1f + Mathf.Clamp(placement.Layer, 0, 12) * 0.018f + global * 0.0008f;
            return new Vector3(-3f + localX, localY, localZ);
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
            if (recipe.Placements != null && recipe.Placements.Count > 0)
            {
                recipe.Scores.Novelty = Mathf.Max(recipe.Scores.Novelty, 92f);
                recipe.Scores.Originality = Mathf.Max(recipe.Scores.Originality, 96f);
            }
            recipe.Scores.Source = "Pizza Connection 3 native citizen ratings + deterministic novelty/originality";
        }
    }
}
