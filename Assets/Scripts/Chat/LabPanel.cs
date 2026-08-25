using creator_ui.LLM;
using creator_ui.Recipe;
using Newtonsoft.Json.Linq;
using System.Collections.Generic;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.UIElements;

namespace creator_ui.Chat
{
    public class LabPanel : MonoBehaviour
    {
        public LLMClient llmClient;
        public NameDialog nameDialog;

        private readonly List<JObject> _recipes = new();
        private JObject? _selected;

        public async Task GenerateBatchAsync(string[] tags)
        {
            var tagStr = string.Join(", ", tags);
            var tasks = new List<Task<JObject>>();
            for (int i = 0; i < 3; i++)
            {
                tasks.Add(GenerateOneAsync($"Tags: {tagStr}. Variant {i + 1}."));
            }
            var results = await Task.WhenAll(tasks);
            _recipes.Clear();
            _recipes.AddRange(results);
            _recipes.Sort((a, b) =>
                (b["scores"]?["taste"]?.Value<double>() ?? 0)
                .CompareTo(a["scores"]?["taste"]?.Value<double>() ?? 0));
            RenderRecipeCards();
        }

        private async Task<JObject> GenerateOneAsync(string prompt)
        {
            var composer = new RecipeComposer(llmClient);
            return await composer.ComposeAsync(
                "Experimental pizza designer. Return Barro's Pizza JSON with 5-8 ingredients.",
                prompt);
        }

        private void RenderRecipeCards()
        {
            var root = GetComponent<UIDocument>().rootVisualElement;
            var scroll = root.Q<ScrollView>("lab__recipes");
            if (scroll == null) return;
            scroll.Clear();
            foreach (var recipe in _recipes)
            {
                var card = new VisualElement();
                card.AddToClassList("card-recipe-card");
                var thumb = new VisualElement();
                thumb.AddToClassList("card-recipe-card__thumb");
                card.Add(thumb);
                var body = new VisualElement();
                body.AddToClassList("card-recipe-card__body");
                var name = new Label((string?)recipe["name"] ?? "Recipe");
                name.AddToClassList("card-recipe-card__name");
                body.Add(name);
                var scores = recipe["scores"];
                if (scores != null)
                {
                    AddScoreRow(body, "Taste", scores["taste"]?.Value<double>() ?? 0);
                    AddScoreRow(body, "Cost", scores["cost_dollars"]?.Value<double>() ?? 0);
                    AddScoreRow(body, "Profit", scores["profit_percent"]?.Value<double>() ?? 0);
                    AddScoreRow(body, "Novelty", scores["novelty"]?.Value<double>() ?? 0);
                }
                card.Add(body);
                var actions = new VisualElement();
                actions.AddToClassList("card-recipe-card__actions");
                var previewBtn = new Button { text = "Preview" };
                previewBtn.AddToClassList("btn");
                previewBtn.AddToClassList("btn-secondary");
                var useBtn = new Button { text = "Use" };
                useBtn.AddToClassList("btn");
                useBtn.AddToClassList("btn-primary");
                var capturedRecipe = recipe;
                useBtn.clicked += () => { _selected = capturedRecipe; nameDialog?.Show(capturedRecipe); };
                actions.Add(previewBtn);
                actions.Add(useBtn);
                card.Add(actions);
                scroll.Add(card);
            }
        }

        private void AddScoreRow(VisualElement parent, string label, double value)
        {
            var row = new VisualElement();
            row.AddToClassList("bar-row");
            var lab = new Label(label);
            lab.AddToClassList("bar-row__label");
            row.Add(lab);
            var track = new VisualElement();
            track.AddToClassList("bar-row__track");
            var fill = new VisualElement();
            fill.AddToClassList("bar__fill");
            fill.style.width = new Length(System.Math.Min(100, value), LengthUnit.Percent);
            track.Add(fill);
            row.Add(track);
            var val = new Label(((int)value).ToString());
            val.AddToClassList("bar-row__value");
            row.Add(val);
            parent.Add(row);
        }
    }
}
