using UnityEngine;
using UnityEngine.UI;

namespace Barros.Creator.UiLab
{
    public sealed class BarrosUiPrototype : MonoBehaviour
    {
        public Button[] tabs;
        public GameObject[] pages;
        public Text pageTitle;
        public Text status;
        public Text listeningIndicator;
        public Slider detailSlider;
        public Toggle voiceToggle;
        public Toggle lyricsToggle;

        private int activeTab;
        private float pulse;

        private static readonly string[] Titles =
        {
            "Pizza Design Chat", "AI Pizza Lab", "Design Crew", "Voice Studio", "Media Deck"
        };

        private static readonly string[] Statuses =
        {
            "Chat is ready to design a pizza with you.",
            "Choose a design idea, detail level, and ingredient palette.",
            "Four agents are ready to take orderly turns.",
            "Microphone and voice controls are ready for testing.",
            "One audio source at a time; lyrics follow playback position."
        };

        private void Start()
        {
            for (int i = 0; i < tabs.Length; i++)
            {
                int captured = i;
                tabs[i].onClick.AddListener(() => SelectTab(captured));
            }
            SelectTab(0);
        }

        private void Update()
        {
            pulse += Time.unscaledDeltaTime * 3f;
            if (listeningIndicator != null)
            {
                float alpha = 0.55f + Mathf.Sin(pulse) * 0.35f;
                listeningIndicator.color = new Color(0.10f, 0.58f, 0.24f, alpha);
            }
        }

        public void SelectTab(int index)
        {
            activeTab = Mathf.Clamp(index, 0, pages.Length - 1);
            for (int i = 0; i < pages.Length; i++) pages[i].SetActive(i == activeTab);
            if (pageTitle != null) pageTitle.text = Titles[activeTab];
            if (status != null) status.text = Statuses[activeTab];
            for (int i = 0; i < tabs.Length; i++)
            {
                ColorBlock colors = tabs[i].colors;
                colors.normalColor = i == activeTab
                    ? new Color(0.43f, 0.12f, 0.13f, 1f)
                    : new Color(0.99f, 0.93f, 0.89f, 1f);
                colors.highlightedColor = new Color(0.68f, 0.16f, 0.18f, 1f);
                tabs[i].colors = colors;
                Text label = tabs[i].GetComponentInChildren<Text>();
                if (label != null) label.color = i == activeTab ? Color.white : new Color(0.18f, 0.13f, 0.12f);
            }
        }

        public void RunPrototypeAction()
        {
            string detail = detailSlider == null ? "high" : Mathf.RoundToInt(detailSlider.value).ToString();
            string voice = voiceToggle != null && voiceToggle.isOn ? "voices on" : "voices muted";
            string lyrics = lyricsToggle != null && lyricsToggle.isOn ? "lyrics on" : "lyrics hidden";
            status.text = "Prototype response passed: detail " + detail + ", " + voice + ", " + lyrics + ".";
        }
    }
}
