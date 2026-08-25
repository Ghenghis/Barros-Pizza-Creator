using creator_ui.LLM;
using creator_ui.Recipe;
using Newtonsoft.Json.Linq;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.UIElements;

namespace creator_ui.Chat
{
    public class DesignerPanel : MonoBehaviour
    {
        public LLMClient llmClient;
        public NameDialog nameDialog;

        private JObject? _currentRecipe;
        private string _mode = "build";

        public void SetMode(string mode) { _mode = mode; }

        public async Task SendAsync(string userText)
        {
            var root = GetComponent<UIDocument>().rootVisualElement;
            var userLabel = root.Q<Label>("designer__msg-user");
            if (userLabel != null) userLabel.text = userText;
            string sysPrompt = _mode switch
            {
                "build" => "You are Barro's AI Pizza Designer. Help the user build a pizza step by step. Return Barro's Pizza JSON.",
                "surprise" => "Invent a surprising but balanced Barro's Pizza. Return Barro's Pizza JSON.",
                "improve" => "Improve the existing recipe by tweaking ingredients/amounts. Return Barro's Pizza JSON.",
                _ => ""
            };
            var composer = new RecipeComposer(llmClient);
            _currentRecipe = await composer.ComposeAsync(sysPrompt, userText);
            UpdateRecipeCard(_currentRecipe);
        }

        private void UpdateRecipeCard(JObject recipe)
        {
            var root = GetComponent<UIDocument>().rootVisualElement;
            var nameLabel = root.Q<Label>("designer__recipe-name");
            if (nameLabel != null) nameLabel.text = (string?)recipe["name"] ?? "Recipe";
            var scores = recipe["scores"];
            if (scores != null)
            {
                var tasteLabel = root.Q<Label>("designer__taste");
                var costLabel = root.Q<Label>("designer__cost");
                var popLabel = root.Q<Label>("designer__pop");
                if (tasteLabel != null) tasteLabel.text = ((int)(scores["taste"]?.Value<double>() ?? 0)).ToString();
                if (costLabel != null) costLabel.text = ((int)((scores["cost_dollars"]?.Value<double>() ?? 0) * 100)).ToString();
                if (popLabel != null) popLabel.text = ((int)(scores["novelty"]?.Value<double>() ?? 0)).ToString();
            }
        }

        public void OnApplyClicked()
        {
            if (_currentRecipe == null) return;
            nameDialog?.Show(_currentRecipe);
        }
    }
}
