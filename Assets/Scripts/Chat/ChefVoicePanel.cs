using creator_ui.LLM;
using creator_ui.Recipe;
using Newtonsoft.Json.Linq;
using System.Linq;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.UIElements;

namespace creator_ui.Chat
{
    public class ChefVoicePanel : MonoBehaviour
    {
        public LLMClient llmClient;
        public NameDialog nameDialog;

        private const string SYSTEM_PROMPT =
            @"You are Chef AI for Barro's Pizza Creator. Help the user design a pizza. Return JSON: { name, dough: {size, shape}, ingredients: [{id, amount_g, position:[x,y,z], rotation:[x,y,z], size}] }. Ingredient IDs MUST be from the catalog.";

        private JObject? _currentRecipe;
        private bool _isComposing;

        private void OnEnable()
        {
            var root = GetComponent<UIDocument>().rootVisualElement;
            var applyBtn = root.Q<Button>("chef-voice__apply");
            if (applyBtn != null) applyBtn.clicked += OnApplyClicked;
            var mildBtn = root.Q<Button>("heat-mild");
            var medBtn = root.Q<Button>("heat-medium");
            var hotBtn = root.Q<Button>("heat-hot");
            if (mildBtn != null) mildBtn.clicked += () => SetHeat("Mild");
            if (medBtn != null) medBtn.clicked += () => SetHeat("Medium");
            if (hotBtn != null) hotBtn.clicked += () => SetHeat("Hot");
        }

        public async Task ComposeAsync(string userText)
        {
            if (_isComposing) return;
            _isComposing = true;
            var root = GetComponent<UIDocument>().rootVisualElement;
            var userLabel = root.Q<Label>("chef-voice__msg-user-text");
            if (userLabel != null) userLabel.text = userText;
            try
            {
                var composer = new RecipeComposer(llmClient);
                _currentRecipe = await composer.ComposeAsync(SYSTEM_PROMPT, userText);
                int ingCount = (_currentRecipe["ingredients"] as JArray)?.Count ?? 0;
                var aiLabel = root.Q<Label>("chef-voice__msg-ai-text");
                if (aiLabel != null) aiLabel.text = $"I can build that. Medium heat or hot? ({ingCount} ingredients)";
                UpdateRecipeCard(_currentRecipe);
            }
            finally { _isComposing = false; }
        }

        private void UpdateRecipeCard(JObject recipe)
        {
            var root = GetComponent<UIDocument>().rootVisualElement;
            var nameLabel = root.Q<Label>("chef-voice__recipe-name");
            if (nameLabel != null) nameLabel.text = (string?)recipe["name"] ?? "Recipe";
            var ingContainer = root.Q<VisualElement>("chef-voice__recipe-ingredients");
            if (ingContainer != null)
            {
                ingContainer.Clear();
                var arr = recipe["ingredients"] as JArray;
                if (arr != null)
                {
                    foreach (var ing in arr)
                    {
                        var row = new Label($"{(string?)ing["id"]} -- {(double?)ing["amount_g"]:0.#}g");
                        row.style.fontSize = 13;
                        ingContainer.Add(row);
                    }
                }
            }
            var scores = recipe["scores"];
            if (scores != null)
            {
                var costLabel = root.Q<Label>("stat-cost");
                var priceLabel = root.Q<Label>("stat-price");
                var profitLabel = root.Q<Label>("stat-profit");
                double cost = scores["cost_dollars"]?.Value<double>() ?? 0;
                if (costLabel != null) costLabel.text = $"Cost ${cost:0.00}";
                if (priceLabel != null) priceLabel.text = $"Price ${cost * 1.5:0.00}";
                if (profitLabel != null) profitLabel.text = $"Profit {scores["profit_percent"]?.Value<double>() ?? 0:0.#}%";
            }
        }

        private void SetHeat(string heat)
        {
            var root = GetComponent<UIDocument>().rootVisualElement;
            var mild = root.Q<Button>("heat-mild");
            var med = root.Q<Button>("heat-medium");
            var hot = root.Q<Button>("heat-hot");
            if (mild != null) mild.EnableInClassList("btn-chip--active", heat == "Mild");
            if (med != null) med.EnableInClassList("btn-chip--active", heat == "Medium");
            if (hot != null) hot.EnableInClassList("btn-chip--active", heat == "Hot");
        }

        private void OnApplyClicked()
        {
            if (_currentRecipe == null) return;
            nameDialog?.Show(_currentRecipe);
        }
    }
}
