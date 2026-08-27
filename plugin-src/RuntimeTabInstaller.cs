using System;
using System.IO;
using BepInEx.Logging;
using UnityEngine;
using UnityEngine.UI;
using UserInterface;

namespace Barros.PizzaCreator.AI
{
    public sealed class RuntimeTabInstaller
    {
        private readonly GameBridge game;
        private readonly BackendClient backend;
        private readonly EvidenceRecorder evidence;
        private readonly ManualLogSource log;
        private Tab aiTab;
        private TabBar tabBar;
        private GameObject content;

        public bool Installed
        {
            get { return aiTab != null && tabBar != null && content != null; }
        }

        public RuntimeTabInstaller(GameBridge gameBridge, BackendClient backendClient, EvidenceRecorder recorder, ManualLogSource logger)
        {
            game = gameBridge;
            backend = backendClient;
            evidence = recorder;
            log = logger;
        }

        public bool TryInstall()
        {
            if (Installed) return true;
            PizzaCreatorTabBar creator = UnityEngine.Object.FindObjectOfType<PizzaCreatorTabBar>();
            if (creator == null || creator.tabbar == null || creator.recipeTab == null || creator.recipeTab.content == null)
                return false;
            try
            {
                tabBar = creator.tabbar;
                Tab source = creator.recipeTab;
                GameObject tabObject = UnityEngine.Object.Instantiate(source.gameObject);
                tabObject.name = "tab_barros_ai_designer";
                RectTransform tabRect = tabObject.GetComponent<RectTransform>();
                tabRect.SetParent(source.transform.parent, false);
                CopyRect(source.GetComponent<RectTransform>(), tabRect);
                tabRect.SetAsLastSibling();
                PlaceAfterExistingTabs(source, tabRect);
                Tab clonedTab = tabObject.GetComponent<Tab>();
                if (clonedTab == null) throw new InvalidOperationException("The native recipe tab clone did not contain a Tab component.");
                if (clonedTab.colorizeElement != null) clonedTab.colorizeElement.gameObject.SetActive(false);
                if (clonedTab.border != null) clonedTab.border.SetActive(false);
                Image sourceImage = source.GetComponent<Image>();
                Image background = tabObject.GetComponent<Image>();
                if (sourceImage != null)
                {
                    background.sprite = sourceImage.sprite;
                    background.type = sourceImage.type;
                    background.material = sourceImage.material;
                    background.color = sourceImage.color;
                }

                GameObject iconObject = new GameObject("AI chef icon", typeof(RectTransform), typeof(CanvasRenderer), typeof(Image));
                RectTransform iconRect = iconObject.GetComponent<RectTransform>();
                iconRect.SetParent(tabRect, false);
                iconRect.anchorMin = new Vector2(0.18f, 0.18f);
                iconRect.anchorMax = new Vector2(0.82f, 0.82f);
                iconRect.offsetMin = Vector2.zero;
                iconRect.offsetMax = Vector2.zero;
                Image icon = iconObject.GetComponent<Image>();
                icon.sprite = CreateChefBubbleSprite();
                icon.preserveAspect = true;
                icon.raycastTarget = false;

                GameObject borderObject = new GameObject("active border", typeof(RectTransform), typeof(CanvasRenderer), typeof(Image));
                RectTransform borderRect = borderObject.GetComponent<RectTransform>();
                borderRect.SetParent(tabRect, false);
                borderRect.anchorMin = new Vector2(0f, 0f);
                borderRect.anchorMax = new Vector2(0.09f, 1f);
                borderRect.offsetMin = Vector2.zero;
                borderRect.offsetMax = Vector2.zero;
                Image borderImage = borderObject.GetComponent<Image>();
                borderImage.color = new Color(0.83f, 0.16f, 0.18f, 1f);
                borderImage.raycastTarget = false;

                content = new GameObject("Barros AI Designer Content", typeof(RectTransform), typeof(CanvasRenderer), typeof(Image));
                RectTransform contentRect = content.GetComponent<RectTransform>();
                contentRect.SetParent(source.content.transform.parent, false);
                CopyRect(source.content.GetComponent<RectTransform>(), contentRect);
                contentRect.SetAsLastSibling();
                Image blocker = content.GetComponent<Image>();
                blocker.color = new Color(0f, 0f, 0f, 0.005f);
                // The IMGUI panel sits over the native Pizza Creator canvas. This
                // transparent image must consume pointer events or a Media/Chat
                // button can also press a hidden stock control underneath it.
                blocker.raycastTarget = true;

                aiTab = clonedTab;
                aiTab.content = content;
                aiTab.border = borderObject;
                aiTab.colorizeElement = icon;
                aiTab.defaultColor = source.defaultColor;
                aiTab.activeColor = source.activeColor;
                aiTab.highlightColor = source.highlightColor;
                aiTab.pressedColor = source.pressedColor;
                aiTab.isOn = false;
                content.SetActive(false);
                tabBar.RegisterTab(aiTab);
                Canvas.ForceUpdateCanvases();
                RectTransform tabParent = tabRect.parent as RectTransform;
                if (tabParent != null) LayoutRebuilder.ForceRebuildLayoutImmediate(tabParent);

                Text header = FindHeader();
                Font font = header != null ? header.font : FindAnyFont(source.gameObject);
                GameObject banner = CreateHeaderBanner(header);
                PanelRenderer renderer = content.AddComponent<PanelRenderer>();
                renderer.Configure(contentRect, aiTab, tabBar, game, backend, evidence, header, banner, font);
                evidence.Record("ui.tab_installed", DescribeRect(tabRect));
                if (banner != null)
                {
                    RectTransform bannerRect = banner.GetComponent<RectTransform>();
                    RectTransform titleParent = header != null ? header.rectTransform.parent as RectTransform : null;
                    float available = titleParent != null ? titleParent.rect.width - 78f : bannerRect.rect.width;
                    bool safe = bannerRect.rect.width <= available + 0.5f;
                    evidence.Record(safe ? "ui.header_fitted" : "ui.header_overlap", "banner_width=" + bannerRect.rect.width.ToString("0.0") + "; safe_width=" + available.ToString("0.0") + "; close_reserve=78");
                }
                log.LogInfo("Installed Barro's AI Designer as a live Pizza Creator tab.");
                return true;
            }
            catch (Exception exception)
            {
                log.LogError("AI tab installation failed: " + exception);
                if (content != null) UnityEngine.Object.Destroy(content);
                content = null;
                aiTab = null;
                tabBar = null;
                return false;
            }
        }

        public void Activate()
        {
            if (Installed) tabBar.ActivateTab(aiTab);
        }

        private static void CopyRect(RectTransform source, RectTransform target)
        {
            if (source == null || target == null) return;
            target.anchorMin = source.anchorMin;
            target.anchorMax = source.anchorMax;
            target.pivot = source.pivot;
            target.anchoredPosition = source.anchoredPosition;
            target.sizeDelta = source.sizeDelta;
            target.localScale = source.localScale;
            target.localRotation = source.localRotation;
        }

        private static string DescribeRect(RectTransform rect)
        {
            if (rect == null) return "null rect";
            return "x=" + rect.anchoredPosition.x.ToString("0.0") + "; y=" + rect.anchoredPosition.y.ToString("0.0") + "; width=" + rect.rect.width.ToString("0.0") + "; height=" + rect.rect.height.ToString("0.0") + "; sibling=" + rect.GetSiblingIndex();
        }

        private static void PlaceAfterExistingTabs(Tab source, RectTransform target)
        {
            if (source == null || target == null || source.transform.parent == null) return;
            Transform parent = source.transform.parent;
            if (parent.GetComponent<LayoutGroup>() != null) return;
            Tab[] siblings = parent.GetComponentsInChildren<Tab>(true);
            RectTransform last = null;
            RectTransform previous = null;
            int lastIndex = -1;
            int previousIndex = -1;
            for (int i = 0; i < siblings.Length; i++)
            {
                if (siblings[i] == null || siblings[i].transform.parent != parent) continue;
                int siblingIndex = siblings[i].transform.GetSiblingIndex();
                RectTransform rect = siblings[i].GetComponent<RectTransform>();
                if (rect == null) continue;
                if (siblingIndex > lastIndex)
                {
                    previous = last;
                    previousIndex = lastIndex;
                    last = rect;
                    lastIndex = siblingIndex;
                }
                else if (siblingIndex > previousIndex)
                {
                    previous = rect;
                    previousIndex = siblingIndex;
                }
            }
            if (last == null) return;
            Vector2 step = new Vector2(0f, -(Mathf.Max(4f, last.rect.height) + 4f));
            if (previous != null)
            {
                Vector2 observed = last.anchoredPosition - previous.anchoredPosition;
                if (observed.sqrMagnitude > 16f) step = observed;
            }
            target.anchoredPosition = last.anchoredPosition + step;
        }

        private static Text FindHeader()
        {
            Text[] texts = UnityEngine.Object.FindObjectsOfType<Text>();
            for (int i = 0; i < texts.Length; i++)
            {
                if (string.Equals(texts[i].text, "Bakehouse", StringComparison.OrdinalIgnoreCase)) return texts[i];
            }
            return null;
        }

        private static Font FindAnyFont(GameObject root)
        {
            Text text = root.GetComponentInChildren<Text>(true);
            if (text != null) return text.font;
            Text[] all = UnityEngine.Object.FindObjectsOfType<Text>();
            return all.Length > 0 ? all[0].font : Resources.GetBuiltinResource<Font>("Arial.ttf");
        }

        private static GameObject CreateHeaderBanner(Text header)
        {
            if (header == null) return null;
            string path = Path.Combine(BepInEx.Paths.GameRootPath, "BarrosAI", "assets", "barros-pizza-creator-header.png");
            if (!File.Exists(path)) return null;
            try
            {
                byte[] bytes = File.ReadAllBytes(path);
                Texture2D texture = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                if (!texture.LoadImage(bytes))
                {
                    UnityEngine.Object.Destroy(texture);
                    return null;
                }
                texture.name = "Barros Pizza Creator Header";
                texture.wrapMode = TextureWrapMode.Clamp;
                texture.filterMode = FilterMode.Bilinear;
                texture.hideFlags = HideFlags.HideAndDontSave;

                GameObject banner = new GameObject("Barros Pizza Creator Header", typeof(RectTransform), typeof(CanvasRenderer), typeof(Image));
                RectTransform rect = banner.GetComponent<RectTransform>();
                rect.SetParent(header.rectTransform, false);
                rect.anchorMin = new Vector2(0f, 0f);
                rect.anchorMax = new Vector2(0f, 1f);
                rect.pivot = new Vector2(0f, 0.5f);
                rect.anchoredPosition = Vector2.zero;
                float width = 470f;
                RectTransform parentRect = header.rectTransform.parent as RectTransform;
                if (parentRect != null && parentRect.rect.width > 200f)
                    width = Mathf.Clamp(parentRect.rect.width - 78f, 280f, 560f);
                rect.sizeDelta = new Vector2(width, 0f);
                Image image = banner.GetComponent<Image>();
                image.sprite = Sprite.Create(texture, new Rect(0f, 0f, texture.width, texture.height), new Vector2(0f, 0.5f), 100f);
                image.preserveAspect = true;
                image.raycastTarget = false;
                banner.SetActive(false);
                return banner;
            }
            catch
            {
                return null;
            }
        }

        private static Sprite CreateChefBubbleSprite()
        {
            const int size = 64;
            Texture2D texture = new Texture2D(size, size, TextureFormat.RGBA32, false);
            Color clear = new Color(0f, 0f, 0f, 0f);
            Color ink = new Color(0.95f, 0.83f, 0.72f, 1f);
            Color[] pixels = new Color[size * size];
            for (int i = 0; i < pixels.Length; i++) pixels[i] = clear;
            texture.SetPixels(pixels);
            for (int y = 7; y < 52; y++)
            {
                for (int x = 7; x < 57; x++)
                {
                    float dx = x - 32f;
                    float dy = y - 30f;
                    float distance = Mathf.Sqrt(dx * dx + dy * dy);
                    if (distance > 22f && distance < 25f) texture.SetPixel(x, y, ink);
                }
            }
            for (int y = 6; y < 18; y++)
                for (int x = 17; x < 30; x++)
                    if (x - 17 < 18 - y) texture.SetPixel(x, y, ink);
            DrawFilledCircle(texture, 23, 34, 9, ink);
            DrawFilledCircle(texture, 32, 30, 11, ink);
            DrawFilledCircle(texture, 41, 34, 9, ink);
            for (int y = 36; y < 48; y++) for (int x = 22; x < 43; x++) texture.SetPixel(x, y, ink);
            for (int y = 39; y < 45; y++) for (int x = 28; x < 37; x++) texture.SetPixel(x, y, clear);
            texture.Apply();
            texture.hideFlags = HideFlags.HideAndDontSave;
            return Sprite.Create(texture, new Rect(0f, 0f, size, size), new Vector2(0.5f, 0.5f));
        }

        private static void DrawFilledCircle(Texture2D texture, int centerX, int centerY, int radius, Color color)
        {
            for (int y = -radius; y <= radius; y++)
                for (int x = -radius; x <= radius; x++)
                    if (x * x + y * y <= radius * radius) texture.SetPixel(centerX + x, centerY + y, color);
        }
    }
}
