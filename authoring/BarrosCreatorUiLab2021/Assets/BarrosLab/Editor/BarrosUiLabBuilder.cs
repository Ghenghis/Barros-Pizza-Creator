using System;
using System.IO;
using UnityEditor;
using UnityEditor.Events;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace Barros.Creator.UiLab.Editor
{
    public static class BarrosUiLabBuilder
    {
        private const string ScenePath = "Assets/BarrosLab/Scenes/BarrosCreatorUiLab.unity";
        private static readonly Color Ink = new Color(0.18f, 0.13f, 0.12f);
        private static readonly Color Parchment = new Color(0.94f, 0.84f, 0.78f);
        private static readonly Color Light = new Color(0.99f, 0.93f, 0.89f);
        private static readonly Color Card = new Color(0.97f, 0.88f, 0.82f);
        private static readonly Color Maroon = new Color(0.43f, 0.12f, 0.13f);
        private static readonly Color Red = new Color(0.68f, 0.16f, 0.18f);
        private static readonly Font Font = Resources.GetBuiltinResource<Font>("Arial.ttf");

        [MenuItem("Barros/1 - Build or Refresh UI Prototype")]
        public static void BuildPrototype()
        {
            GenerateSkins();
            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            CreateEventSystem();
            CreatePreviewCamera();

            Canvas canvas = CreateCanvas();
            RectTransform root = canvas.GetComponent<RectTransform>();
            CreateImage("Game Backdrop", root, new Color(0.075f, 0.08f, 0.085f), 0, 0, 1920, 1080, null);
            CreateText("Game Title", root, "PIZZA CONNECTION 3 — BARRO'S CREATOR UI LAB", 32, FontStyle.Bold,
                Color.white, TextAnchor.MiddleLeft, 30, 18, 1100, 52);
            CreateText("Resolution Note", root, "Safe preview: 1920 × 1080 • the original game is represented, not copied", 16,
                FontStyle.Normal, new Color(0.72f, 0.75f, 0.77f), TextAnchor.MiddleLeft, 30, 70, 880, 30);

            BuildProtectedGameRail(root);
            BarrosUiPrototype controller = BuildBarrosPanel(root);
            Selection.activeGameObject = controller.gameObject;

            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath));
            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("BARROS_UI_LAB_OK scene=" + ScenePath + " size=1920x1080 tabs=5");
        }

        public static void BuildAndExportFromCommandLine()
        {
            try
            {
                BuildPrototype();
                BarrosUiCompatibilityExporter.ExportCompatibilityPack();
                Debug.Log("BARROS_UI_LAB_BATCH_OK");
                EditorApplication.Exit(0);
            }
            catch (Exception ex)
            {
                Debug.LogException(ex);
                EditorApplication.Exit(1);
            }
        }

        private static Canvas CreateCanvas()
        {
            GameObject go = new GameObject("Barros UI Lab Canvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            Canvas canvas = go.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            CanvasScaler scaler = go.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;
            return canvas;
        }

        private static void CreateEventSystem()
        {
            new GameObject("EventSystem", typeof(EventSystem), typeof(StandaloneInputModule));
        }

        private static void CreatePreviewCamera()
        {
            GameObject go = new GameObject("UI Lab Preview Camera", typeof(Camera));
            Camera camera = go.GetComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.075f, 0.08f, 0.085f);
            camera.orthographic = true;
            camera.transform.position = new Vector3(0, 0, -10);
        }

        private static void BuildProtectedGameRail(RectTransform root)
        {
            RectTransform rail = CreateImage("Protected Original Five Tabs", root, new Color(0.12f, 0.13f, 0.14f),
                24, 120, 220, 840, LoadSkin("card"));
            CreateText("Rail Heading", rail, "ORIGINAL GAME TABS", 15, FontStyle.Bold, new Color(0.95f, 0.75f, 0.33f),
                TextAnchor.MiddleCenter, 12, 14, 196, 36);
            string[] labels = { "Base", "Sauce", "Cheese", "Toppings", "Bake" };
            for (int i = 0; i < labels.Length; i++)
            {
                Button button = CreateButton("Game Tab " + (i + 1), rail, (i + 1) + "   " + labels[i],
                    18, 70 + i * 92, 184, 64, LoadSkin("button"));
                button.interactable = false;
            }
            CreateText("Protected Note", rail,
                "This rail must remain visible. The add-on panel is always fitted beside it.", 15, FontStyle.Normal,
                new Color(0.76f, 0.79f, 0.81f), TextAnchor.UpperLeft, 18, 570, 184, 150);
        }

        private static BarrosUiPrototype BuildBarrosPanel(RectTransform root)
        {
            RectTransform panel = CreateImage("Barros Add-on Safe Panel", root, Parchment, 1260, 18, 640, 1044, LoadSkin("panel"));
            BarrosUiPrototype controller = panel.gameObject.AddComponent<BarrosUiPrototype>();
            controller.pageTitle = CreateText("Page Title", panel, "Pizza Design Chat", 27, FontStyle.Bold, Ink,
                TextAnchor.MiddleLeft, 18, 12, 405, 38);

            RectTransform connection = CreateImage("Connection", panel, Card, 438, 14, 180, 30, LoadSkin("card"));
            CreateText("Connection Dot", connection, "●", 20, FontStyle.Bold, new Color(0.12f, 0.60f, 0.25f),
                TextAnchor.MiddleCenter, 4, 1, 26, 26);
            CreateText("Connection Text", connection, "Local provider ready", 13, FontStyle.Normal, Ink,
                TextAnchor.MiddleLeft, 30, 2, 145, 25);

            string[] tabLabels = { "Chat", "AI Lab", "Crew", "Voice", "Media" };
            controller.tabs = new Button[tabLabels.Length];
            for (int i = 0; i < tabLabels.Length; i++)
                controller.tabs[i] = CreateButton("Mode " + tabLabels[i], panel, tabLabels[i], 16 + i * 121, 55, 114, 39, LoadSkin("button"));

            controller.pages = new GameObject[tabLabels.Length];
            controller.pages[0] = BuildPage(panel, "Chat Page", "Design together",
                "Tell the assistant what the pizza should look like. It asks useful questions before changing the recipe.",
                new[] { "User: Make a detailed Arizona sunset pizza.", "Barro's AI: Should the sun be pepperoni or tomato?", "✓ Draft stays editable until you approve it." });
            controller.pages[1] = BuildPage(panel, "AI Lab Page", "Smart ingredient placement",
                "Choose a recognizable subject, then map its colors and shapes to real ingredients.",
                new[] { "Template: Santa Claus", "Palette: Classic red, white and green", "Detail: High • placement preview enabled" });
            controller.pages[2] = BuildPage(panel, "Crew Page", "Four-agent roundtable",
                "Flavor, cost, customer and creative agents take turns without talking over each other.",
                new[] { "Flavor Chef: balance heat with sweetness", "Cost Manager: keep the target margin", "Creative Director: preserve the face silhouette" });
            controller.pages[3] = BuildPage(panel, "Voice Page", "Hands-free design",
                "Select a microphone, test its level, and assign distinct Azure voices to the design crew.",
                new[] { "● Microphone detected", "Agent voices begin muted", "Music pauses before an agent speaks" });
            controller.pages[4] = BuildPage(panel, "Media Page", "Music and synchronized lyrics",
                "Search, queue and reorder Barro's songs. Only one source plays and lyrics follow pause, resume and seek.",
                new[] { "Now playing: Barros Calling Casa Grande", "Lyrics video: fitted portrait preview", "Queue: no duplicate audio sources" });
            for (int i = 0; i < controller.pages.Length; i++) controller.pages[i].SetActive(i == 0);

            RectTransform controls = CreateImage("Prototype Controls", panel, Light, 14, 858, 612, 170, LoadSkin("card"));
            CreateText("Control Heading", controls, "LIVE PROTOTYPE CONTROLS", 14, FontStyle.Bold, Maroon,
                TextAnchor.MiddleLeft, 14, 8, 260, 26);
            CreateText("Detail Label", controls, "Design detail", 14, FontStyle.Normal, Ink,
                TextAnchor.MiddleLeft, 14, 42, 100, 24);
            controller.detailSlider = CreateSlider("Detail Slider", controls, 115, 45, 180, 20);
            controller.voiceToggle = CreateToggle("Voice Toggle", controls, "Agent voices", 315, 39, 130, 30);
            controller.lyricsToggle = CreateToggle("Lyrics Toggle", controls, "Show lyrics", 455, 39, 130, 30);
            controller.lyricsToggle.isOn = true;
            Button run = CreateButton("Run Prototype Test", controls, "RUN PROTOTYPE RESPONSE", 14, 78, 280, 42, LoadSkin("primary"));
            UnityEventTools.AddPersistentListener(run.onClick, controller.RunPrototypeAction);
            controller.listeningIndicator = CreateText("Listening Pulse", controls, "●", 25, FontStyle.Bold,
                new Color(0.12f, 0.60f, 0.25f), TextAnchor.MiddleCenter, 309, 83, 34, 34);
            CreateText("Listening Label", controls, "interaction preview", 13, FontStyle.Normal, Ink,
                TextAnchor.MiddleLeft, 345, 86, 180, 28);
            controller.status = CreateText("Status", controls, "Chat is ready to design a pizza with you.", 13,
                FontStyle.Normal, Ink, TextAnchor.MiddleLeft, 14, 125, 575, 32);
            return controller;
        }

        private static GameObject BuildPage(RectTransform panel, string name, string heading, string description, string[] cards)
        {
            RectTransform page = CreateImage(name, panel, new Color(0, 0, 0, 0), 14, 105, 612, 735, null);
            CreateText("Heading", page, heading, 22, FontStyle.Bold, Maroon, TextAnchor.MiddleLeft, 12, 10, 560, 34);
            CreateText("Description", page, description, 16, FontStyle.Normal, Ink, TextAnchor.UpperLeft, 12, 52, 570, 62);
            for (int i = 0; i < cards.Length; i++)
            {
                RectTransform card = CreateImage("Card " + (i + 1), page, Card, 12, 132 + i * 142, 570, 116, LoadSkin("card"));
                CreateText("Card Text", card, cards[i], 17, i == 2 ? FontStyle.Bold : FontStyle.Normal, Ink,
                    TextAnchor.MiddleLeft, 18, 12, 530, 92);
            }
            CreateText("Safe Area Proof", page,
                "✓ 640 × 1050 virtual panel  •  ✓ five tabs visible  •  ✓ content scroll-safe at 1080p",
                14, FontStyle.Bold, new Color(0.12f, 0.55f, 0.24f), TextAnchor.MiddleCenter, 12, 590, 570, 52);
            return page.gameObject;
        }

        private static RectTransform CreateImage(string name, Transform parent, Color color, float x, float y, float width, float height, Sprite sprite)
        {
            GameObject go = new GameObject(name, typeof(RectTransform), typeof(Image));
            go.transform.SetParent(parent, false);
            RectTransform rect = go.GetComponent<RectTransform>();
            Place(rect, x, y, width, height);
            Image image = go.GetComponent<Image>();
            image.color = color;
            image.sprite = sprite;
            image.type = sprite == null ? Image.Type.Simple : Image.Type.Sliced;
            return rect;
        }

        private static Text CreateText(string name, Transform parent, string value, int size, FontStyle style, Color color,
            TextAnchor anchor, float x, float y, float width, float height)
        {
            GameObject go = new GameObject(name, typeof(RectTransform), typeof(Text));
            go.transform.SetParent(parent, false);
            Place(go.GetComponent<RectTransform>(), x, y, width, height);
            Text text = go.GetComponent<Text>();
            text.font = Font;
            text.fontSize = size;
            text.fontStyle = style;
            text.color = color;
            text.alignment = anchor;
            text.text = value;
            text.horizontalOverflow = HorizontalWrapMode.Wrap;
            text.verticalOverflow = VerticalWrapMode.Truncate;
            return text;
        }

        private static Button CreateButton(string name, Transform parent, string label, float x, float y, float width, float height, Sprite sprite)
        {
            RectTransform rect = CreateImage(name, parent, Color.white, x, y, width, height, sprite);
            Button button = rect.gameObject.AddComponent<Button>();
            ColorBlock colors = button.colors;
            colors.normalColor = Light;
            colors.highlightedColor = Red;
            colors.pressedColor = Maroon;
            colors.disabledColor = new Color(0.28f, 0.29f, 0.30f, 0.8f);
            button.colors = colors;
            CreateText("Label", rect, label, 14, FontStyle.Bold, Ink, TextAnchor.MiddleCenter, 5, 3, width - 10, height - 6);
            return button;
        }

        private static Slider CreateSlider(string name, Transform parent, float x, float y, float width, float height)
        {
            RectTransform root = CreateImage(name, parent, new Color(0, 0, 0, 0), x, y, width, height, null);
            RectTransform background = CreateImage("Background", root, new Color(0.75f, 0.65f, 0.60f), 0, 6, width, 8, LoadSkin("button"));
            RectTransform fill = CreateImage("Fill", root, Red, 0, 6, width, 8, LoadSkin("primary"));
            RectTransform handle = CreateImage("Handle", root, Maroon, width * 0.65f - 8, 0, 16, 20, LoadSkin("primary"));
            Slider slider = root.gameObject.AddComponent<Slider>();
            slider.fillRect = fill;
            slider.handleRect = handle;
            slider.targetGraphic = handle.GetComponent<Image>();
            slider.minValue = 1;
            slider.maxValue = 10;
            slider.wholeNumbers = true;
            slider.value = 7;
            return slider;
        }

        private static Toggle CreateToggle(string name, Transform parent, string label, float x, float y, float width, float height)
        {
            RectTransform root = CreateImage(name, parent, new Color(0, 0, 0, 0), x, y, width, height, null);
            RectTransform box = CreateImage("Background", root, Light, 0, 5, 20, 20, LoadSkin("button"));
            RectTransform check = CreateImage("Checkmark", box, Red, 4, 4, 12, 12, LoadSkin("primary"));
            Toggle toggle = root.gameObject.AddComponent<Toggle>();
            toggle.targetGraphic = box.GetComponent<Image>();
            toggle.graphic = check.GetComponent<Image>();
            CreateText("Label", root, label, 13, FontStyle.Normal, Ink, TextAnchor.MiddleLeft, 28, 0, width - 28, height);
            return toggle;
        }

        private static void Place(RectTransform rect, float x, float y, float width, float height)
        {
            rect.anchorMin = rect.anchorMax = new Vector2(0, 1);
            rect.pivot = new Vector2(0, 1);
            rect.anchoredPosition = new Vector2(x, -y);
            rect.sizeDelta = new Vector2(width, height);
        }

        private static Sprite LoadSkin(string name)
        {
            return AssetDatabase.LoadAssetAtPath<Sprite>("Assets/BarrosLab/Generated/" + name + ".png");
        }

        private static void GenerateSkins()
        {
            string directory = Path.Combine(Application.dataPath, "BarrosLab/Generated");
            Directory.CreateDirectory(directory);
            WriteRoundedSkin(Path.Combine(directory, "panel.png"), Parchment, new Color(0.50f, 0.29f, 0.25f, 0.62f), 16);
            WriteRoundedSkin(Path.Combine(directory, "card.png"), Card, new Color(0.57f, 0.37f, 0.32f, 0.50f), 14);
            WriteRoundedSkin(Path.Combine(directory, "button.png"), Light, new Color(0.57f, 0.37f, 0.32f, 0.50f), 13);
            WriteRoundedSkin(Path.Combine(directory, "active.png"), Maroon, new Color(0.30f, 0.09f, 0.08f), 13);
            WriteRoundedSkin(Path.Combine(directory, "primary.png"), Red, new Color(0.43f, 0.08f, 0.08f), 13);
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            foreach (string file in Directory.GetFiles(directory, "*.png"))
            {
                string assetPath = "Assets" + file.Replace(Application.dataPath, "").Replace('\\', '/');
                TextureImporter importer = AssetImporter.GetAtPath(assetPath) as TextureImporter;
                if (importer == null) continue;
                importer.textureType = TextureImporterType.Sprite;
                importer.spriteImportMode = SpriteImportMode.Single;
                importer.spriteBorder = new Vector4(18, 18, 18, 18);
                importer.mipmapEnabled = false;
                importer.alphaIsTransparency = true;
                importer.SaveAndReimport();
            }
        }

        private static void WriteRoundedSkin(string path, Color fill, Color border, int radius)
        {
            const int size = 64;
            Texture2D texture = new Texture2D(size, size, TextureFormat.RGBA32, false);
            for (int y = 0; y < size; y++)
            for (int x = 0; x < size; x++)
            {
                float px = x + 0.5f;
                float py = y + 0.5f;
                float nx = Mathf.Clamp(px, radius, size - radius);
                float ny = Mathf.Clamp(py, radius, size - radius);
                float distance = Vector2.Distance(new Vector2(px, py), new Vector2(nx, ny));
                float alpha = Mathf.Clamp01(radius + 0.5f - distance);
                Color pixel = distance > radius - 2 ? border : fill;
                pixel.a *= alpha;
                texture.SetPixel(x, y, pixel);
            }
            texture.Apply();
            File.WriteAllBytes(path, texture.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(texture);
        }
    }
}
