using UnityEngine;
using UnityEngine.UIElements;

namespace creator_ui.Sidebar
{
    public class TabNavigator : MonoBehaviour
    {
        public UIDocument document;
        public VisualTreeAsset chefVoicePanel;
        public VisualTreeAsset crewPanel;
        public VisualTreeAsset labPanel;
        public VisualTreeAsset designerPanel;

        private VisualElement _contentRoot;
        private string _activeTab = "chef-voice";

        public string ActiveTab => _activeTab;

        private void OnEnable()
        {
            if (document == null || document.rootVisualElement == null) return;
            var root = document.rootVisualElement;
            _contentRoot = root.Q<VisualElement>("content-root");
            if (_contentRoot == null) return;
            WireButton(root, "tab-chef-voice", "chef-voice");
            WireButton(root, "tab-crew", "crew");
            WireButton(root, "tab-lab", "lab");
            WireButton(root, "tab-designer", "designer");
            SwitchTo(_activeTab);
        }

        private void WireButton(VisualElement root, string btnName, string tabName)
        {
            var btn = root.Q<Button>(btnName);
            if (btn != null) btn.clicked += () => SwitchTo(tabName);
        }

        public void SwitchTo(string tab)
        {
            _activeTab = tab;
            if (_contentRoot == null) return;
            _contentRoot.Clear();
            var asset = tab switch
            {
                "chef-voice" => chefVoicePanel,
                "crew" => crewPanel,
                "lab" => labPanel,
                "designer" => designerPanel,
                _ => chefVoicePanel
            };
            if (asset != null) _contentRoot.Add(asset.Instantiate());

            var root = document.rootVisualElement;
            foreach (var tabName in new[] { "chef-voice", "crew", "lab", "designer" })
            {
                var btn = root.Q<Button>($"tab-{tabName}");
                if (btn != null) btn.EnableInClassList("sidebar__icon--active", tabName == tab);
            }
        }
    }
}
