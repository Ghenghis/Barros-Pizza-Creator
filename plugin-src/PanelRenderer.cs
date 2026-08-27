using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.UI;
using UserInterface;

namespace Barros.PizzaCreator.AI
{
    public sealed class PanelRenderer : MonoBehaviour
    {
        private const float VirtualWidth = 640f;
        private const float VirtualHeight = 1050f;
        private readonly Color parchment = new Color(0.91f, 0.74f, 0.63f, 1f);
        private readonly Color parchmentLight = new Color(0.98f, 0.87f, 0.79f, 1f);
        private readonly Color card = new Color(0.96f, 0.82f, 0.73f, 1f);
        private readonly Color maroon = new Color(0.43f, 0.12f, 0.13f, 1f);
        private readonly Color red = new Color(0.68f, 0.16f, 0.18f, 1f);
        private readonly Color ink = new Color(0.18f, 0.13f, 0.12f, 1f);
        private readonly Color green = new Color(0.12f, 0.60f, 0.25f, 1f);
        private readonly Color amber = new Color(0.92f, 0.58f, 0.08f, 1f);

        private RectTransform panelRect;
        private Tab tab;
        private TabBar tabBar;
        private GameBridge game;
        private BackendClient backend;
        private EvidenceRecorder evidence;
        private Text gameHeader;
        private GameObject headerBanner;
        private string originalHeader = "Bakehouse";
        private Font gameFont;
        private DesignerMode mode = DesignerMode.Chat;
        private string chatAction = "Build with me";
        private string prompt = "Make a bold Arizona pizza, spicy but not extreme.";
        private string heat = "Medium";
        private string shape = "Round";
        private float priceCeiling = 14f;
        private float profitFactor = 0.6f;
        private bool busy;
        private bool backendReady;
        private string backendLabel = "Connecting";
        private string status = "Describe a pizza, ask for a surprise, or improve what is on the board.";
        private bool showHistory = true;
        private bool editRecipe;
        private Vector2 scroll;
        private readonly List<ConversationLine> conversation = new List<ConversationLine>();
        private readonly List<AiRecipe> recipes = new List<AiRecipe>();
        private readonly List<AiAgentOpinion> agents = new List<AiAgentOpinion>();
        private readonly List<AiAttachment> attachments = new List<AiAttachment>();
        private AiConsensus consensus;
        private int selectedRecipe;
        private AudioClip voiceClip;
        private bool recording;
        private float recordingStarted;
        private string transcript = "";
        private string pendingVoiceError = "";

        private GUIStyle panelStyle;
        private GUIStyle cardStyle;
        private GUIStyle titleStyle;
        private GUIStyle subtitleStyle;
        private GUIStyle bodyStyle;
        private GUIStyle smallStyle;
        private GUIStyle buttonStyle;
        private GUIStyle activeButtonStyle;
        private GUIStyle primaryButtonStyle;
        private GUIStyle inputStyle;
        private GUIStyle tagStyle;
        private GUIStyle speakerStyle;
        private GUIStyle scoreStyle;
        private Texture2D parchmentTexture;
        private Texture2D cardTexture;
        private Texture2D maroonTexture;
        private Texture2D redTexture;
        private Texture2D lightTexture;
        private Texture2D greenTexture;
        private Texture2D amberTexture;
        private Texture2D whiteTexture;

        public DesignerMode Mode { get { return mode; } }

        public void Configure(RectTransform rect, Tab ownerTab, TabBar ownerBar, GameBridge bridge, BackendClient client, EvidenceRecorder recorder, Text header, GameObject banner, Font font)
        {
            panelRect = rect;
            tab = ownerTab;
            tabBar = ownerBar;
            game = bridge;
            backend = client;
            evidence = recorder;
            gameHeader = header;
            headerBanner = banner;
            gameFont = font;
            if (gameHeader != null) originalHeader = gameHeader.text;
            if (headerBanner != null) headerBanner.SetActive(false);
            conversation.Add(new ConversationLine("Barro's AI", "Tell me what kind of pizza you want. I will use only ingredients installed in this Creator build."));
            backend.Health(delegate(bool ready, string label)
            {
                backendReady = ready;
                backendLabel = ready ? label : "Backend unavailable";
                if (!ready) status = "The local AI service is not responding. Run DIAGNOSE_Barros_AI.ps1.";
            });
            backend.History(delegate(List<ConversationLine> earlier)
            {
                if (earlier == null || earlier.Count == 0) return;
                conversation.InsertRange(0, earlier);
            });
        }

        private void OnEnable()
        {
            SetHeaderActive(true);
            if (evidence != null) StartCoroutine(CaptureInitialUi());
        }

        private void OnDisable()
        {
            SetHeaderActive(false);
            if (evidence != null)
            {
                evidence.Record("ui.stock_header_restored", originalHeader);
                evidence.Capture("ui-stock-header");
            }
        }

        private void Update()
        {
            if (recording && Time.realtimeSinceStartup - recordingStarted >= 29.5f) StopVoiceAndTranscribe();
            if (Input.GetKeyDown(KeyCode.F8) && evidence != null) evidence.Capture(ModeFileName());
        }

        private IEnumerator CaptureInitialUi()
        {
            yield return null;
            yield return new WaitForEndOfFrame();
            evidence.Capture("ui-tab");
            evidence.Capture("ui-header");
        }

        private string ModeFileName()
        {
            if (mode == DesignerMode.Lab) return "lab";
            if (mode == DesignerMode.Crew) return "crew";
            if (mode == DesignerMode.Voice) return "voice";
            return "chat";
        }

        private void OnGUI()
        {
            if (tab == null || !tab.isOn || panelRect == null) return;
            EnsureStyles();
            Rect screenRect = GetScreenRect(panelRect);
            if (screenRect.width < 200f || screenRect.height < 300f)
                screenRect = new Rect(Screen.width * 0.69f, 60f, Screen.width * 0.31f, Screen.height - 60f);
            Matrix4x4 previous = GUI.matrix;
            Color previousColor = GUI.color;
            bool previousEnabled = GUI.enabled;
            GUI.matrix = Matrix4x4.TRS(
                new Vector3(screenRect.x, screenRect.y, 0f),
                Quaternion.identity,
                new Vector3(screenRect.width / VirtualWidth, screenRect.height / VirtualHeight, 1f));
            try
            {
                DrawPanel();
            }
            finally
            {
                GUI.matrix = previous;
                GUI.color = previousColor;
                GUI.enabled = previousEnabled;
            }
        }

        private void DrawPanel()
        {
            GUI.Box(new Rect(0f, 0f, VirtualWidth, VirtualHeight), GUIContent.none, panelStyle);
            GUI.Label(new Rect(18f, 10f, 410f, 38f), HeaderForMode(), titleStyle);
            DrawConnection(new Rect(438f, 14f, 180f, 28f));
            string[] labels = { "Chat", "AI Lab", "Design Crew", "Chef Voice" };
            for (int i = 0; i < labels.Length; i++)
            {
                Rect modeRect = new Rect(16f + i * 153f, 55f, 145f, 39f);
                GUIStyle style = (int)mode == i ? activeButtonStyle : buttonStyle;
                string modeHelp = i == 0 ? "Chat step by step with the Barro's pizza designer."
                    : i == 1 ? "Generate and compare three game-valid ideas."
                    : i == 2 ? "Ask the four specialist agents for a balanced draft."
                    : "Use the Windows microphone, then review the transcript before applying.";
                if (GUI.Button(modeRect, Help(labels[i], modeHelp), style)) SetMode((DesignerMode)i);
            }

            Rect content = new Rect(14f, 105f, 612f, 755f);
            GUILayout.BeginArea(content);
            scroll = GUILayout.BeginScrollView(scroll, false, true);
            if (mode == DesignerMode.Chat) DrawChat();
            else if (mode == DesignerMode.Lab) DrawLab();
            else if (mode == DesignerMode.Crew) DrawCrew();
            else DrawVoice();
            GUILayout.Space(12f);
            GUILayout.EndScrollView();
            GUILayout.EndArea();

            DrawComposer(new Rect(14f, 868f, 612f, 168f));
            DrawHoverHelp();
        }

        private static GUIContent Help(string label, string tooltip)
        {
            return new GUIContent(label, tooltip);
        }

        private void DrawHoverHelp()
        {
            string tooltip = GUI.tooltip;
            if (string.IsNullOrEmpty(tooltip)) return;
            GUI.Box(new Rect(14f, 832f, 612f, 29f), GUIContent.none, cardStyle);
            GUI.Label(new Rect(24f, 837f, 592f, 20f), tooltip, smallStyle);
        }

        private void DrawConnection(Rect rect)
        {
            GUI.Box(rect, GUIContent.none, cardStyle);
            Color old = GUI.color;
            GUI.color = Color.white;
            GUI.DrawTexture(new Rect(rect.x + 9f, rect.y + 8f, 12f, 12f), backendReady ? greenTexture : amberTexture);
            GUI.color = old;
            GUI.Label(new Rect(rect.x + 28f, rect.y + 3f, rect.width - 33f, 22f), backendLabel, smallStyle);
        }

        private void SetMode(DesignerMode next)
        {
            mode = next;
            scroll = Vector2.zero;
            if (gameHeader != null && headerBanner == null) gameHeader.text = HeaderForMode();
        }

        private string HeaderForMode()
        {
            if (mode == DesignerMode.Lab) return "AI Pizza Lab";
            if (mode == DesignerMode.Crew) return "Barro's Design Crew";
            if (mode == DesignerMode.Voice) return "Chef Voice";
            return "Barro's AI Pizza Designer";
        }

        private void SetHeaderActive(bool active)
        {
            if (headerBanner != null) headerBanner.SetActive(active);
            if (gameHeader == null) return;
            gameHeader.text = active ? (headerBanner == null ? HeaderForMode() : "") : originalHeader;
        }

        private void DrawChat()
        {
            GUILayout.BeginHorizontal();
            string[] actions = { "Build with me", "Surprise me", "Improve this" };
            for (int i = 0; i < actions.Length; i++)
            {
                GUIStyle style = chatAction == actions[i] ? activeButtonStyle : buttonStyle;
                string actionHelp = i == 0 ? "Build a validated pizza with your guidance."
                    : i == 1 ? "Ask for a distinctive game-valid draft automatically."
                    : "Improve the current pizza while preserving its main idea.";
                if (GUILayout.Button(Help(actions[i], actionHelp), style, GUILayout.Height(36f))) chatAction = actions[i];
            }
            GUILayout.EndHorizontal();
            GUILayout.Space(8f);
            if (showHistory)
            {
                for (int i = 0; i < conversation.Count; i++) DrawConversationLine(conversation[i]);
            }
            if (recipes.Count > 0)
            {
                GUILayout.Space(8f);
                DrawRecipeCard(recipes[Mathf.Clamp(selectedRecipe, 0, recipes.Count - 1)], true, true);
            }
            else
            {
                GUILayout.Box("Start with a request such as:\n\n“Use chicken, bacon and jalapeno; medium heat; keep it profitable.”\n\nThe recipe card will show exact in-game ingredients, real cost, native citizen taste, popularity, novelty and originality.", cardStyle, GUILayout.ExpandWidth(true), GUILayout.MinHeight(220f));
            }
        }

        private void DrawConversationLine(ConversationLine line)
        {
            GUILayout.BeginVertical(cardStyle);
            GUILayout.Label(line.Speaker, speakerStyle);
            GUILayout.Label(line.Text, bodyStyle);
            GUILayout.Label(line.Time.ToString("h:mm tt"), smallStyle);
            GUILayout.EndVertical();
            GUILayout.Space(4f);
        }

        private void DrawLab()
        {
            GUILayout.BeginVertical(cardStyle);
            GUILayout.Label("What should I invent?", subtitleStyle);
            GUILayout.BeginHorizontal();
            GUILayout.Label("Heat: " + heat, tagStyle);
            GUILayout.Label("Shape: " + shape, tagStyle);
            GUILayout.Label("Under $" + priceCeiling.ToString("0"), tagStyle);
            GUILayout.EndHorizontal();
            GUILayout.BeginHorizontal();
            GUILayout.Label("Price ceiling", smallStyle);
            if (GUILayout.Button("−", buttonStyle, GUILayout.Width(42f), GUILayout.Height(30f))) priceCeiling = Mathf.Max(4f, priceCeiling - 1f);
            GUILayout.Label("$" + priceCeiling.ToString("0.00"), speakerStyle, GUILayout.Width(85f));
            if (GUILayout.Button("+", buttonStyle, GUILayout.Width(42f), GUILayout.Height(30f))) priceCeiling = Mathf.Min(50f, priceCeiling + 1f);
            GUILayout.FlexibleSpace();
            GUILayout.EndHorizontal();
            if (GUILayout.Button(Help("SURPRISE ME — GENERATE 3", "Generate three validated candidates from the selected heat, shape and price limits."), primaryButtonStyle, GUILayout.Height(52f)))
            {
                if (string.IsNullOrEmpty(prompt)) prompt = "Create three distinctive crowd-pleasing pizzas.";
                Submit("/lab", 3);
            }
            GUILayout.EndVertical();
            GUILayout.Space(8f);
            if (recipes.Count == 0)
            {
                GUILayout.Box("Three valid alternatives will appear here with taste, cost, profit, popularity, novelty and native preview controls.", cardStyle, GUILayout.MinHeight(150f));
            }
            for (int i = 0; i < recipes.Count; i++)
            {
                selectedRecipe = Mathf.Clamp(selectedRecipe, 0, recipes.Count - 1);
                DrawLabCandidate(recipes[i], i);
            }
            if (recipes.Count > 0)
            {
                GUILayout.BeginVertical(cardStyle);
                GUILayout.Label("Why it works", subtitleStyle);
                GUILayout.Label(recipes[selectedRecipe].Rationale, bodyStyle);
                if (GUILayout.Button(Help("Generate 3 more", "Keep the same constraints and request three different candidates."), buttonStyle, GUILayout.Height(38f))) Submit("/lab", 3);
                GUILayout.EndVertical();
            }
        }

        private void DrawLabCandidate(AiRecipe recipe, int index)
        {
            GUILayout.BeginVertical(index == selectedRecipe ? cardStyle : panelStyle);
            GUILayout.BeginHorizontal();
            GUILayout.Label(recipe.Name, subtitleStyle);
            GUILayout.FlexibleSpace();
            if (GUILayout.Button(Help("Preview", "Temporarily show this candidate on the live pizza without saving it."), buttonStyle, GUILayout.Width(104f), GUILayout.Height(34f))) Preview(recipe, index);
            if (GUILayout.Button(Help("Use", "Apply this validated candidate to the live Creator editor; saving remains a separate action."), primaryButtonStyle, GUILayout.Width(90f), GUILayout.Height(34f))) Apply(recipe, index);
            GUILayout.EndHorizontal();
            DrawCompactScore("Taste", recipe.Scores.Taste, green);
            DrawCompactScore("Cost", CostScore(recipe.Scores.Cost), amber);
            DrawCompactScore("Profit", recipe.Scores.Profit, green);
            DrawCompactScore("Novelty", recipe.Scores.Novelty, green);
            GUILayout.Label(recipe.Summary, smallStyle);
            GUILayout.EndVertical();
            GUILayout.Space(6f);
        }

        private void DrawCrew()
        {
            if (agents.Count == 0)
            {
                GUILayout.BeginVertical(cardStyle);
                GUILayout.Label("4 agents ready", subtitleStyle);
                DrawAgentReady("Flavor Chef", "Suggesting bold, craveable combinations.");
                DrawAgentReady("Cost Manager", "Keeping ingredients efficient.");
                DrawAgentReady("Customer Scout", "Tracking broad preferences.");
                DrawAgentReady("Creative Director", "Ensuring a unique signature.");
                if (GUILayout.Button(Help("ASK THE CREW", "Ask Flavor, Cost, Customer and Creative agents to produce one reconciled draft."), primaryButtonStyle, GUILayout.Height(52f))) Submit("/crew", 1);
                GUILayout.EndVertical();
                return;
            }
            for (int i = 0; i < agents.Count; i++) DrawAgentReady(agents[i].Agent, agents[i].Message);
            GUILayout.Space(6f);
            GUILayout.BeginVertical(cardStyle);
            GUILayout.Label("Crew consensus", subtitleStyle);
            if (consensus != null)
            {
                GUILayout.Label(consensus.Name, titleStyle);
                DrawCompactScore("Flavor", consensus.Flavor, red);
                DrawCompactScore("Profit", consensus.Profit, red);
                DrawCompactScore("Popularity", consensus.Popularity, red);
                DrawCompactScore("Originality", consensus.Originality, red);
                GUILayout.Label("Consensus " + consensus.Score.ToString("0") + "%", speakerStyle);
            }
            GUILayout.EndVertical();
            GUILayout.Space(6f);
            GUILayout.BeginVertical(cardStyle);
            GUILayout.Label("Crew discussion", subtitleStyle);
            for (int i = 0; i < agents.Count; i++)
            {
                GUILayout.Label(agents[i].Agent + "  " + agents[i].Score.ToString("0"), speakerStyle);
                GUILayout.Label(agents[i].Message, smallStyle);
                GUILayout.Space(5f);
            }
            GUILayout.EndVertical();
            if (recipes.Count > 0)
            {
                GUILayout.BeginHorizontal();
                if (GUILayout.Button(Help("Balanced", "Balance live game cost and score facts without claiming a stock optimum."), buttonStyle, GUILayout.Height(35f))) ApplyCrewPreset("balanced");
                if (GUILayout.Button(Help("Max flavor", "Prefer the crew's flavor direction, then recompute with live game services."), activeButtonStyle, GUILayout.Height(35f))) ApplyCrewPreset("flavor");
                if (GUILayout.Button(Help("Max profit", "Prefer lower cost and a higher profit factor, then recompute live facts."), buttonStyle, GUILayout.Height(35f))) ApplyCrewPreset("profit");
                GUILayout.EndHorizontal();
                if (GUILayout.Button(Help("APPLY CREW RECIPE", "Apply the validated crew draft to the editor. This does not save automatically."), primaryButtonStyle, GUILayout.Height(52f))) Apply(recipes[0], 0);
            }
        }

        private void DrawAgentReady(string name, string detail)
        {
            GUILayout.BeginHorizontal(cardStyle);
            GUILayout.Label(name, speakerStyle, GUILayout.Width(155f));
            GUILayout.Label(detail, smallStyle);
            GUILayout.Label("✓", speakerStyle, GUILayout.Width(25f));
            GUILayout.EndHorizontal();
            GUILayout.Space(3f);
        }

        private void DrawVoice()
        {
            GUILayout.BeginVertical(cardStyle);
            GUILayout.BeginHorizontal();
            GUILayout.Label("Chef Voice", titleStyle);
            GUILayout.FlexibleSpace();
            GUILayout.Label(recording ? "● Listening" : "Ready", recording ? speakerStyle : smallStyle);
            GUILayout.EndHorizontal();
            Rect waveRect = GUILayoutUtility.GetRect(560f, 112f, GUILayout.ExpandWidth(true));
            DrawWaveform(waveRect);
            string micLabel = recording ? "STOP & TRANSCRIBE" : "START LISTENING";
            if (GUILayout.Button(Help(micLabel, "Record from the Windows default microphone for up to 30 seconds, then transcribe for review."), recording ? activeButtonStyle : primaryButtonStyle, GUILayout.Height(52f)))
            {
                if (recording) StopVoiceAndTranscribe(); else StartVoice();
            }
            GUILayout.Label("Tell me what kind of pizza you want", subtitleStyle);
            GUILayout.EndVertical();
            GUILayout.Space(6f);
            if (!string.IsNullOrEmpty(transcript))
            {
                GUILayout.BeginVertical(cardStyle);
                GUILayout.Label("You", speakerStyle);
                GUILayout.Label(transcript, bodyStyle);
                GUILayout.EndVertical();
            }
            if (!string.IsNullOrEmpty(pendingVoiceError)) GUILayout.Label(pendingVoiceError, speakerStyle);
            GUILayout.BeginVertical(cardStyle);
            GUILayout.Label("Heat level", subtitleStyle);
            GUILayout.BeginHorizontal();
            string[] heats = { "Mild", "Medium", "Hot" };
            for (int i = 0; i < heats.Length; i++)
            {
                if (GUILayout.Button(heats[i], heat == heats[i] ? activeButtonStyle : buttonStyle, GUILayout.Height(36f))) heat = heats[i];
            }
            GUILayout.EndHorizontal();
            GUILayout.EndVertical();
            if (recipes.Count > 0) DrawRecipeCard(recipes[0], true, true);
        }

        private void DrawWaveform(Rect rect)
        {
            GUI.Box(rect, GUIContent.none, panelStyle);
            float phase = Time.realtimeSinceStartup * (recording ? 6f : 1.2f);
            for (int i = 0; i < 35; i++)
            {
                float value = recording ? Mathf.Abs(Mathf.Sin(phase + i * 0.7f) * Mathf.Cos(i * 0.31f)) : 0.15f;
                float height = 12f + value * (rect.height - 24f);
                GUI.color = recording ? red : new Color(0.55f, 0.32f, 0.29f, 1f);
                GUI.DrawTexture(new Rect(rect.x + 10f + i * ((rect.width - 20f) / 35f), rect.center.y - height * 0.5f, 3f, height), whiteTexture);
            }
            GUI.color = Color.white;
        }

        private void DrawRecipeCard(AiRecipe recipe, bool showScores, bool showActions)
        {
            GUILayout.BeginVertical(cardStyle);
            GUILayout.BeginHorizontal();
            GUILayout.Label(recipe.Name, titleStyle);
            GUILayout.FlexibleSpace();
            GUILayout.Label(recipe.Shape, tagStyle);
            if (GUILayout.Button(Help(editRecipe ? "DONE" : "EDIT", "Edit planning grams, piece size and placement distribution before preview."), editRecipe ? activeButtonStyle : buttonStyle, GUILayout.Width(72f), GUILayout.Height(31f))) editRecipe = !editRecipe;
            GUILayout.EndHorizontal();
            GUILayout.Label(recipe.Summary, bodyStyle);
            GUILayout.Space(5f);
            for (int i = 0; i < recipe.Ingredients.Count; i++)
            {
                AiRecipeIngredient ingredient = recipe.Ingredients[i];
                GUILayout.BeginHorizontal();
                GUILayout.Label("• " + ingredient.Id, bodyStyle, GUILayout.Width(245f));
                GUILayout.Label(ingredient.Size, smallStyle, GUILayout.Width(85f));
                GUILayout.Label(ingredient.TargetGrams.ToString("0") + " g target", smallStyle);
                GUILayout.EndHorizontal();
                if (editRecipe)
                {
                    GUILayout.BeginHorizontal();
                    GUILayout.Space(18f);
                    if (GUILayout.Button("−10 g", buttonStyle, GUILayout.Width(75f), GUILayout.Height(27f))) { ingredient.TargetGrams = Mathf.Max(1f, ingredient.TargetGrams - 10f); Recalculate(recipe); }
                    if (GUILayout.Button("+10 g", buttonStyle, GUILayout.Width(75f), GUILayout.Height(27f))) { ingredient.TargetGrams += 10f; Recalculate(recipe); }
                    if (GUILayout.Button("Size: " + ingredient.Size, buttonStyle, GUILayout.Width(115f), GUILayout.Height(27f))) { ingredient.Size = NextSize(ingredient.Size); Recalculate(recipe); }
                    if (GUILayout.Button(ingredient.Distribution, buttonStyle, GUILayout.Width(110f), GUILayout.Height(27f))) { ingredient.Distribution = NextDistribution(ingredient.Distribution); Recalculate(recipe); }
                    GUILayout.EndHorizontal();
                }
            }
            GUILayout.Label(recipe.Rationale, smallStyle);
            if (showScores)
            {
                GUILayout.Space(6f);
                GUILayout.BeginHorizontal();
                ScoreTile("Taste", recipe.Scores.Taste, false);
                ScoreTile("Cost", recipe.Scores.Cost, true);
                ScoreTile("Profit", recipe.Scores.Profit, false);
                GUILayout.EndHorizontal();
                GUILayout.BeginHorizontal();
                ScoreTile("Popularity", recipe.Scores.Popularity, false);
                ScoreTile("Novelty", recipe.Scores.Novelty, false);
                ScoreTile("Originality", recipe.Scores.Originality, false);
                GUILayout.EndHorizontal();
            }
            if (showActions)
            {
                GUILayout.BeginHorizontal();
                if (GUILayout.Button(Help("PREVIEW ON PIZZA", "Temporarily load this draft into the live pizza editor without saving."), buttonStyle, GUILayout.Height(48f))) Preview(recipe, recipes.IndexOf(recipe));
                if (GUILayout.Button(Help("APPLY RECIPE", "Apply the validated recipe to the editor. Use Save separately after review."), primaryButtonStyle, GUILayout.Height(48f))) Apply(recipe, recipes.IndexOf(recipe));
                GUILayout.EndHorizontal();
                GUILayout.BeginHorizontal();
                if (GUILayout.Button(Help("Save to recipe book", "Use the Creator's native recipe save service and retain the save receipt."), buttonStyle, GUILayout.Height(38f))) SaveToBook();
                if (GUILayout.Button(Help("Export stock JPG", "Use the Creator's stock ScreenCapture path; the JPG is visual output, not editable recipe data."), buttonStyle, GUILayout.Height(38f))) ExportJpeg();
                if (GUILayout.Button(Help("Start over", "Clear the AI draft and attachments; it does not delete a saved stock recipe."), buttonStyle, GUILayout.Height(38f))) StartOver();
                GUILayout.EndHorizontal();
            }
            GUILayout.EndVertical();
        }

        private void ScoreTile(string label, float value, bool money)
        {
            GUILayout.BeginVertical(cardStyle, GUILayout.MinWidth(170f));
            GUILayout.Label(label, smallStyle);
            GUILayout.Label(money ? "$" + value.ToString("0.00") : value.ToString("0"), scoreStyle);
            GUILayout.EndVertical();
        }

        private void DrawCompactScore(string label, float value, Color color)
        {
            Rect rect = GUILayoutUtility.GetRect(570f, 22f, GUILayout.ExpandWidth(true));
            GUI.Label(new Rect(rect.x, rect.y, 94f, 22f), label, smallStyle);
            Rect track = new Rect(rect.x + 94f, rect.y + 5f, rect.width - 137f, 11f);
            GUI.color = new Color(0.75f, 0.65f, 0.59f, 1f);
            GUI.DrawTexture(track, lightTexture);
            GUI.color = color;
            GUI.DrawTexture(new Rect(track.x, track.y, track.width * Mathf.Clamp01(value / 100f), track.height), whiteTexture);
            GUI.color = Color.white;
            GUI.Label(new Rect(rect.xMax - 38f, rect.y, 38f, 22f), value.ToString("0"), smallStyle);
        }

        private float CostScore(float cost)
        {
            return Mathf.Clamp(100f - cost * 4f, 5f, 100f);
        }

        private void DrawComposer(Rect rect)
        {
            GUI.Box(rect, GUIContent.none, cardStyle);
            GUI.Label(new Rect(rect.x + 10f, rect.y + 7f, rect.width - 20f, 22f), status, smallStyle);
            prompt = GUI.TextArea(new Rect(rect.x + 10f, rect.y + 33f, rect.width - 130f, 77f), prompt, 800, inputStyle);
            GUI.enabled = !busy && game != null && game.Ready;
            if (GUI.Button(new Rect(rect.x + rect.width - 111f, rect.y + 33f, 101f, 77f), Help(busy ? "WORKING…" : "SEND  ➜", "Send the prompt and current live catalog/constraints to the configured local sidecar."), primaryButtonStyle))
            {
                if (mode == DesignerMode.Lab) Submit("/lab", 3);
                else if (mode == DesignerMode.Crew) Submit("/crew", 1);
                else Submit("/chat", 1);
            }
            GUI.enabled = true;
            if (GUI.Button(new Rect(rect.x + 10f, rect.y + 119f, 78f, 39f), Help("Attach", "Attach a PNG, JPEG, WebP or supported text reference; files are validated before use."), buttonStyle)) Attach();
            if (GUI.Button(new Rect(rect.x + 94f, rect.y + 119f, 76f, 39f), Help(recording ? "Stop mic" : "Mic", "Use the Windows default microphone; keyboard input always remains available."), buttonStyle))
            {
                if (recording) StopVoiceAndTranscribe(); else StartVoice();
            }
            if (GUI.Button(new Rect(rect.x + 176f, rect.y + 119f, 93f, 39f), Help("History", "Show or hide earlier prompts retained by the local sidecar."), showHistory ? activeButtonStyle : buttonStyle)) showHistory = !showHistory;
            if (GUI.Button(new Rect(rect.x + 275f, rect.y + 119f, 91f, 39f), Help(shape, "Cycle among the exact four Creator dough-shape contracts."), buttonStyle)) CycleShape();
            if (GUI.Button(new Rect(rect.x + 372f, rect.y + 119f, 88f, 39f), Help(heat, "Cycle the requested heat preference; this is a user constraint, not a stock score."), buttonStyle)) CycleHeat();
            string attachmentText = attachments.Count == 0 ? "No files" : attachments.Count + " attached";
            GUI.Label(new Rect(rect.x + 467f, rect.y + 126f, 132f, 28f), attachmentText, smallStyle);
        }

        private void Submit(string endpoint, int count)
        {
            if (busy) return;
            if (!backendReady)
            {
                backend.Health(delegate(bool ready, string label)
                {
                    backendReady = ready;
                    backendLabel = ready ? label : "Backend unavailable";
                    if (ready) Submit(endpoint, count);
                    else status = "Local AI backend is not running. Use the diagnostic script.";
                });
                return;
            }
            string effective = prompt.Trim();
            if (chatAction == "Surprise me" && endpoint == "/chat") effective = "Surprise me with a distinctive, game-valid pizza. " + effective;
            if (chatAction == "Improve this" && endpoint == "/chat") effective = "Improve the current pizza while preserving its idea. " + effective;
            if (string.IsNullOrEmpty(effective)) effective = "Surprise me with a distinctive crowd favorite.";
            AiRequest request = new AiRequest();
            request.Prompt = effective;
            request.Count = count;
            request.Catalog = game.BuildCatalog();
            request.CurrentPizza = game.DescribeCurrentPizza();
            request.Constraints.Heat = heat;
            request.Constraints.Shape = shape;
            request.Constraints.PriceCeiling = priceCeiling;
            request.Constraints.ProfitFactor = profitFactor;
            request.Attachments.AddRange(attachments);
            conversation.Add(new ConversationLine("You", effective));
            busy = true;
            status = endpoint == "/crew" ? "The four agents are debating…" : "Designing and validating against the live catalog…";
            backend.Compose(endpoint, request, delegate(AiResponse response)
            {
                busy = false;
                if (response == null || !response.Ok)
                {
                    status = response == null ? "No response from backend." : response.Error;
                    conversation.Add(new ConversationLine("Barro's AI", status));
                    return;
                }
                recipes.Clear();
                for (int i = 0; i < response.Recipes.Count; i++)
                {
                    try { recipes.Add(game.Prepare(response.Recipes[i])); }
                    catch (Exception exception) { status = "Recipe validation failed: " + exception.Message; }
                }
                agents.Clear();
                if (response.Agents != null) agents.AddRange(response.Agents);
                consensus = response.Consensus;
                selectedRecipe = 0;
                attachments.Clear();
                status = response.Message;
                conversation.Add(new ConversationLine("Barro's AI", response.Message));
                if (recipes.Count > 0) conversation.Add(new ConversationLine("Barro's AI", "Drafted “" + recipes[0].Name + "”. Preview it on the real dough or apply it."));
            });
        }

        private void Recalculate(AiRecipe recipe)
        {
            try
            {
                game.Prepare(recipe);
                status = "Updated portions and recalculated using the game model.";
            }
            catch (Exception exception) { status = "Edit failed: " + exception.Message; }
        }

        private void ApplyCrewPreset(string preset)
        {
            if (recipes.Count == 0) return;
            AiRecipe recipe = recipes[0];
            if (preset == "flavor")
            {
                recipe.ProfitFactor = 0.45f;
                for (int i = 0; i < recipe.Ingredients.Count; i++)
                    recipe.Ingredients[i].TargetGrams = Mathf.Min(recipe.Ingredients[i].TargetGrams * 1.12f, recipe.Ingredients[i].TargetGrams + 50f);
                status = "Flavor-forward portions selected; the live candidate was rebuilt.";
            }
            else if (preset == "profit")
            {
                recipe.ProfitFactor = 1.0f;
                for (int i = 0; i < recipe.Ingredients.Count; i++)
                    recipe.Ingredients[i].TargetGrams = Mathf.Max(1f, recipe.Ingredients[i].TargetGrams * 0.84f);
                status = "Profit-forward portions selected; the live candidate was rebuilt.";
            }
            else
            {
                recipe.ProfitFactor = 0.6f;
                status = "Balanced margin selected; the live candidate was rebuilt.";
            }
            profitFactor = recipe.ProfitFactor;
            Recalculate(recipe);
        }

        private static string NextSize(string value)
        {
            return value == "Large" ? "Medium" : (value == "Medium" ? "Small" : "Large");
        }

        private static string NextDistribution(string value)
        {
            string[] values = { "even", "center", "ring", "edge", "random", "spiral", "artistic" };
            for (int i = 0; i < values.Length; i++)
                if (string.Equals(values[i], value, StringComparison.OrdinalIgnoreCase)) return values[(i + 1) % values.Length];
            return "even";
        }

        private void Preview(AiRecipe recipe, int index)
        {
            try
            {
                selectedRecipe = Mathf.Max(0, index);
                game.Preview(recipe);
                status = "Previewing “" + recipe.Name + "” on the live pizza. Start over restores the previous pizza.";
                StartCoroutine(ReactivateAiTab("preview"));
            }
            catch (Exception exception) { status = "Preview failed: " + exception.Message; }
        }

        private void Apply(AiRecipe recipe, int index)
        {
            try
            {
                selectedRecipe = Mathf.Max(0, index);
                game.Apply(recipe);
                status = "Applied “" + recipe.Name + "” with real placed ingredients. Use the game's Save button when ready.";
                conversation.Add(new ConversationLine("Barro's AI", status));
                StartCoroutine(ReactivateAiTab("apply"));
            }
            catch (Exception exception) { status = "Apply failed: " + exception.Message; }
        }

        private void StartOver()
        {
            try
            {
                bool restored = game.Restore();
                recipes.Clear();
                agents.Clear();
                consensus = null;
                status = restored ? "Restored the pizza from before the AI preview." : "Cleared the AI draft.";
                if (restored) StartCoroutine(ReactivateAiTab("restore"));
            }
            catch (Exception exception) { status = "Restore failed: " + exception.Message; }
        }

        private void SaveToBook()
        {
            try
            {
                game.SaveCurrentToRecipeBook();
                status = "Saved and verified the native recipe JSON: " + game.SavedRecipePath;
                StartCoroutine(ReactivateAiTab());
            }
            catch (Exception exception) { status = "Save failed: " + exception.Message; }
        }

        private void ExportJpeg()
        {
            try
            {
                string path = game.ExportCurrentJpeg();
                status = "Exported with the stock Pizza Creator JPG pipeline: " + path;
            }
            catch (Exception exception) { status = "JPG export failed: " + exception.Message; }
        }

        private IEnumerator ReactivateAiTab(string captureName = "")
        {
            yield return null;
            yield return null;
            if (tabBar != null && tab != null) tabBar.ActivateTab(tab);
            yield return new WaitForSeconds(0.35f);
            if (tabBar != null && tab != null) tabBar.ActivateTab(tab);
            if (evidence != null && !string.IsNullOrEmpty(captureName))
            {
                yield return new WaitForEndOfFrame();
                evidence.Capture(captureName);
            }
        }

        private void Attach()
        {
            try
            {
                string path = FileDialog.PickAttachment();
                if (string.IsNullOrEmpty(path)) return;
                AiAttachment attachment = FileDialog.ReadAttachment(path);
                if (attachments.Count >= 3) attachments.RemoveAt(0);
                attachments.Add(attachment);
                status = "Attached " + attachment.Name + ". Vision-capable providers can inspect images.";
            }
            catch (Exception exception) { status = "Attachment failed: " + exception.Message; }
        }

        private void StartVoice()
        {
            pendingVoiceError = "";
            if (Microphone.devices == null || Microphone.devices.Length == 0)
            {
                pendingVoiceError = "Windows did not report a microphone.";
                status = pendingVoiceError;
                if (evidence != null) evidence.Record("voice.capture.failed", pendingVoiceError);
                return;
            }
            try
            {
                voiceClip = Microphone.Start(null, false, 30, 16000);
                recording = voiceClip != null;
                recordingStarted = Time.realtimeSinceStartup;
                status = recording ? "Listening… click Stop when finished." : "Could not start the microphone.";
                if (evidence != null) evidence.Record(recording ? "voice.capture.started" : "voice.capture.failed", "devices=" + Microphone.devices.Length + "; rate=16000");
                mode = DesignerMode.Voice;
                if (gameHeader != null && headerBanner == null) gameHeader.text = HeaderForMode();
            }
            catch (Exception exception)
            {
                pendingVoiceError = exception.Message;
                status = "Microphone failed: " + exception.Message;
                if (evidence != null) evidence.Record("voice.capture.failed", exception.Message);
            }
        }

        private void StopVoiceAndTranscribe()
        {
            if (!recording || voiceClip == null) return;
            recording = false;
            int position = Mathf.Max(1, Microphone.GetPosition(null));
            Microphone.End(null);
            AudioClip trimmed = AudioClip.Create("BarrosVoice", position, voiceClip.channels, voiceClip.frequency, false);
            float[] samples = new float[position * voiceClip.channels];
            voiceClip.GetData(samples, 0);
            trimmed.SetData(samples, 0);
            byte[] wav = WavEncoder.Encode(trimmed);
            if (evidence != null) evidence.Record("voice.capture.success", "samples=" + samples.Length + "; wav_bytes=" + wav.Length + "; rate=" + voiceClip.frequency);
            Destroy(trimmed);
            Destroy(voiceClip);
            voiceClip = null;
            busy = true;
            status = "Transcribing voice…";
            backend.Transcribe(wav, delegate(TranscriptionResponse response)
            {
                busy = false;
                if (response == null || !response.Ok || string.IsNullOrEmpty(response.Text))
                {
                    pendingVoiceError = response == null ? "No transcription response." : response.Error;
                    status = pendingVoiceError;
                    if (evidence != null) evidence.Record("voice.transcription.failed", pendingVoiceError);
                    return;
                }
                transcript = response.Text;
                prompt = transcript;
                conversation.Add(new ConversationLine("You (voice)", transcript));
                status = "Voice transcribed. Building the recipe…";
                if (evidence != null) evidence.Record("voice.transcription.success", "characters=" + transcript.Length);
                Submit("/chat", 1);
            });
        }

        private void CycleHeat()
        {
            heat = heat == "Mild" ? "Medium" : (heat == "Medium" ? "Hot" : "Mild");
        }

        private void CycleShape()
        {
            shape = shape == "Round" ? "Square" : (shape == "Square" ? "Star" : (shape == "Star" ? "Triangle" : "Round"));
        }

        private Rect GetScreenRect(RectTransform transformValue)
        {
            Vector3[] corners = new Vector3[4];
            transformValue.GetWorldCorners(corners);
            Canvas canvas = transformValue.GetComponentInParent<Canvas>();
            Camera camera = canvas != null && canvas.renderMode != RenderMode.ScreenSpaceOverlay ? canvas.worldCamera : null;
            Vector2 bottomLeft = RectTransformUtility.WorldToScreenPoint(camera, corners[0]);
            Vector2 topRight = RectTransformUtility.WorldToScreenPoint(camera, corners[2]);
            return new Rect(bottomLeft.x, Screen.height - topRight.y, topRight.x - bottomLeft.x, topRight.y - bottomLeft.y);
        }

        private void EnsureStyles()
        {
            if (panelStyle != null) return;
            parchmentTexture = Solid(parchment);
            cardTexture = Solid(card);
            maroonTexture = Solid(maroon);
            redTexture = Solid(red);
            lightTexture = Solid(parchmentLight);
            greenTexture = Solid(green);
            amberTexture = Solid(amber);
            whiteTexture = Solid(Color.white);
            Font font = gameFont != null ? gameFont : Resources.GetBuiltinResource<Font>("Arial.ttf");
            panelStyle = BoxStyle(parchmentTexture, 10, font);
            cardStyle = BoxStyle(cardTexture, 10, font);
            titleStyle = LabelStyle(font, 26, FontStyle.Bold, ink);
            subtitleStyle = LabelStyle(font, 19, FontStyle.Bold, ink);
            bodyStyle = LabelStyle(font, 15, FontStyle.Normal, ink);
            bodyStyle.wordWrap = true;
            smallStyle = LabelStyle(font, 13, FontStyle.Normal, new Color(0.30f, 0.22f, 0.20f));
            smallStyle.wordWrap = true;
            speakerStyle = LabelStyle(font, 15, FontStyle.Bold, red);
            scoreStyle = LabelStyle(font, 23, FontStyle.Bold, green);
            buttonStyle = ButtonStyle(lightTexture, maroonTexture, font, ink);
            activeButtonStyle = ButtonStyle(maroonTexture, redTexture, font, Color.white);
            primaryButtonStyle = ButtonStyle(redTexture, maroonTexture, font, Color.white);
            inputStyle = new GUIStyle(GUI.skin.textArea);
            inputStyle.font = font;
            inputStyle.fontSize = 15;
            inputStyle.wordWrap = true;
            inputStyle.padding = new RectOffset(10, 10, 8, 8);
            inputStyle.normal.background = lightTexture;
            inputStyle.normal.textColor = ink;
            tagStyle = new GUIStyle(buttonStyle);
            tagStyle.fontSize = 12;
            tagStyle.alignment = TextAnchor.MiddleCenter;
        }

        private GUIStyle BoxStyle(Texture2D background, int padding, Font font)
        {
            GUIStyle style = new GUIStyle(GUI.skin.box);
            style.normal.background = background;
            style.normal.textColor = ink;
            style.font = font;
            style.fontSize = 15;
            style.wordWrap = true;
            style.alignment = TextAnchor.UpperLeft;
            style.padding = new RectOffset(padding, padding, padding, padding);
            style.margin = new RectOffset(2, 2, 2, 2);
            return style;
        }

        private GUIStyle LabelStyle(Font font, int size, FontStyle fontStyle, Color color)
        {
            GUIStyle style = new GUIStyle(GUI.skin.label);
            style.font = font;
            style.fontSize = size;
            style.fontStyle = fontStyle;
            style.normal.textColor = color;
            style.richText = false;
            return style;
        }

        private GUIStyle ButtonStyle(Texture2D normal, Texture2D active, Font font, Color color)
        {
            GUIStyle style = new GUIStyle(GUI.skin.button);
            style.font = font;
            style.fontSize = 14;
            style.fontStyle = FontStyle.Bold;
            style.alignment = TextAnchor.MiddleCenter;
            style.normal.background = normal;
            style.hover.background = active;
            style.active.background = active;
            style.focused.background = active;
            style.normal.textColor = color;
            style.hover.textColor = Color.white;
            style.active.textColor = Color.white;
            style.padding = new RectOffset(8, 8, 6, 6);
            style.margin = new RectOffset(2, 2, 2, 2);
            return style;
        }

        private Texture2D Solid(Color color)
        {
            Texture2D texture = new Texture2D(2, 2, TextureFormat.RGBA32, false);
            texture.SetPixels(new Color[] { color, color, color, color });
            texture.Apply();
            texture.hideFlags = HideFlags.HideAndDontSave;
            return texture;
        }
    }
}
