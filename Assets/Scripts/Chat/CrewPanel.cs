using creator_ui.LLM;
using creator_ui.Recipe;
using System.Collections.Generic;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.UIElements;

namespace creator_ui.Chat
{
    public class CrewPanel : MonoBehaviour
    {
        public LLMClient llmClient;
        public NameDialog nameDialog;

        private RecipeData _currentRecipe;
        private readonly List<(string agent, string message, bool warning)> _discussion = new();

        private const string FLAVOR_CHEF_SYS = "You are Flavor Chef. Suggest bold, craveable pizza combinations. One short sentence.";
        private const string COST_MANAGER_SYS = "You are Cost Manager. Flag the cost concern. One short sentence.";
        private const string CUSTOMER_SCOUT_SYS = "You are Customer Scout. Note a trend. One short sentence.";
        private const string CREATIVE_DIRECTOR_SYS = "You are Creative Director. Suggest a name and signature. One short sentence.";

        public async Task ComposeAsync(string theme)
        {
            _discussion.Clear();
            var tasks = new List<Task<string>>
            {
                llmClient.CompleteAsync(FLAVOR_CHEF_SYS, $"Theme: {theme}. Suggest 1 bold ingredient."),
                llmClient.CompleteAsync(COST_MANAGER_SYS, $"Theme: {theme}. Flag cost concern."),
                llmClient.CompleteAsync(CUSTOMER_SCOUT_SYS, $"Theme: {theme}. Note trend."),
                llmClient.CompleteAsync(CREATIVE_DIRECTOR_SYS, $"Theme: {theme}. Suggest name + signature.")
            };
            var results = await Task.WhenAll(tasks);
            _discussion.Add(("Flavor Chef", results[0], false));
            _discussion.Add(("Cost Manager", results[1], true));
            _discussion.Add(("Customer Scout", results[2], false));
            _discussion.Add(("Creative Director", results[3], false));
            UpdateDiscussionLog();

            var composer = new RecipeComposer(llmClient);
            _currentRecipe = await composer.ComposeAsync(
                "Combine the 4 agent suggestions into one Barro's Pizza JSON. Return PizzaModel-shaped JSON.",
                $"Theme: {theme}. Ideas: {string.Join(" | ", results)}");
            UpdateConsensus(_currentRecipe);
        }

        private void UpdateDiscussionLog()
        {
            var root = GetComponent<UIDocument>().rootVisualElement;
            var log = root.Q<ScrollView>("crew__discussion-log");
            if (log == null) return;
            log.Clear();
            foreach (var (agent, msg, warn) in _discussion)
            {
                var row = new VisualElement();
                row.style.flexDirection = FlexDirection.Row;
                row.style.marginBottom = 4;
                var name = new Label(agent);
                name.style.width = 120;
                name.style.unityFontStyleAndWeight = FontStyle.Bold;
                if (warn) name.style.color = Color.red;
                var text = new Label(msg);
                text.style.flexGrow = 1;
                text.style.whiteSpace = WhiteSpace.Normal;
                row.Add(name);
                row.Add(text);
                log.Add(row);
            }
        }

        private void UpdateConsensus(RecipeData recipe)
        {
            var root = GetComponent<UIDocument>().rootVisualElement;
            var nameLabel = root.Q<Label>("crew__pizza-name");
            if (nameLabel != null) nameLabel.text = string.IsNullOrEmpty(recipe.name) ? "Proposed" : recipe.name;
            if (recipe.scores == null) return;
            SetBar(root, "bar-flavor", "bar-flavor-val", recipe.scores.taste);
            SetBar(root, "bar-profit", "bar-profit-val", recipe.scores.profit_percent);
            SetBar(root, "bar-popularity", "bar-popularity-val", 75);
            SetBar(root, "bar-originality", "bar-originality-val", recipe.scores.novelty);
        }

        private void SetBar(VisualElement root, string barName, string valName, float value)
        {
            var bar = root.Q<VisualElement>(barName);
            if (bar != null) bar.style.width = new Length(Mathf.Min(100, value), LengthUnit.Percent);
            var valLabel = root.Q<Label>(valName);
            if (valLabel != null) valLabel.text = ((int)value).ToString();
        }
    }
}
