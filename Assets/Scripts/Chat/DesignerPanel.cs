using creator_ui.LLM;
using creator_ui.Recipe;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.UIElements;

namespace creator_ui.Chat
{
    public class DesignerPanel : MonoBehaviour
    {
        public LLMClient llmClient;
        public NameDialog nameDialog;

        private RecipeData _currentRecipe;
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

        private void UpdateRecipeCard(RecipeData recipe)
        {
            var root = GetComponent<UIDocument>().rootVisualElement;
            var nameLabel = root.Q<Label>("designer__recipe-name");
            if (nameLabel != null) nameLabel.text = string.IsNullOrEmpty(recipe.name) ? "Recipe" : recipe.name;
            if (recipe.scores != null)
            {
                var tasteLabel = root.Q<Label>("designer__taste");
                var costLabel = root.Q<Label>("designer__cost");
                var popLabel = root.Q<Label>("designer__pop");
                if (tasteLabel != null) tasteLabel.text = ((int)recipe.scores.taste).ToString();
                if (costLabel != null) costLabel.text = ((int)(recipe.scores.cost_dollars * 100)).ToString();
                if (popLabel != null) popLabel.text = ((int)recipe.scores.novelty).ToString();
            }
        }

        public void OnApplyClicked()
        {
            if (_currentRecipe == null) return;
            nameDialog?.Show(_currentRecipe);
        }
    }
}
