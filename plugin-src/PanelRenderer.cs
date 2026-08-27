using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json;
using UnityEngine;
using UnityEngine.UI;
using UserInterface;

namespace Barros.PizzaCreator.AI
{
    public sealed class PanelRenderer : MonoBehaviour
    {
        private const float VirtualWidth = 640f;
        private const float VirtualHeight = 1050f;
        // Keep the recovered mock-up's warm parchment character without the
        // heavy orange cast that made adjacent cards feel like hard boxes.
        private readonly Color parchment = new Color(0.94f, 0.84f, 0.78f, 1f);
        private readonly Color parchmentLight = new Color(0.99f, 0.93f, 0.89f, 1f);
        private readonly Color card = new Color(0.97f, 0.88f, 0.82f, 1f);
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
        private bool layoutEvidenceRecorded;
        private bool useInspirationLibrary;
        private string artDetail = "High";
        private string artStyle = "Precision";
        private string artPalette = "Classic";
        private string artTemplate = "Santa";
        private int artSeed;
        private string crewFocusAgent = "";
        private bool sttConfigured;
        private bool ttsConfigured;
        private bool agentVoicesMuted = true;
        private bool agentSpeechBusy;
        private AudioSource agentAudioSource;
        private AudioClip agentSpeechClip;
        private Coroutine agentSpeechRoutine;
        private readonly List<AgentSpeechTurn> agentSpeechQueue = new List<AgentSpeechTurn>();
        private string currentSpeakingAgent = "";
        private bool agentSpeechFocusHeld;
        private bool agentSpeechHasPlayed;
        private int agentSpeechGeneration;
        private float agentVoiceVolume = 0.9f;
        private float agentSpeechRate = 1f;
        private float agentSpeechGap = 0.45f;
        private MediaDeck mediaDeck;
        private bool musicImportBusy;
        private float nextMusicInboxCheck;
        private long lastMusicInboxRevision;
        private Vector2 mediaLibraryScroll;
        private string mediaSearch = "";
        private int mediaFilterMode;
        private int mediaSortMode;
        private string playlistNameDraft = "New Mix";
        private string playlistDeleteArmed = "";
        private int selectedMicrophone;
        private string selectedMicrophoneName = "";
        private bool microphoneMuted;
        private float microphoneGain = 1f;
        private bool voiceUseCrew = true;
        private bool voiceAutoContinue;
        private bool promptFromVoice;
        private bool voiceResumeAfterSpeech;
        private Coroutine voiceResumeRoutine;
        // Compact is the safe default at 1080p. The user can still expand the
        // portrait lyric video without pushing the remaining controls offscreen.
        private bool mediaVideoExpanded;
        private readonly Dictionary<string, int> agentVoiceIndexes = new Dictionary<string, int>();
        private readonly List<AiRecipe> designCheckpoints = new List<AiRecipe>();
        private bool checkpointCompare;
        private string artSymmetry = "Mirror";
        private string lastPizzaDna = "Generate a design to reveal its Pizza DNA.";
        private int guidedStepCount = 8;
        private int guidedStep;
        private bool guidedActive;
        private string guidedTone = "Playful";
        private readonly List<string> guidedAnswers = new List<string>();
        private bool guidedBuildPending;

        private static readonly string[] VoiceNames =
        {
            "en-US-AvaNeural", "en-US-AndrewNeural", "en-US-JennyNeural", "en-US-GuyNeural",
            "en-GB-SoniaNeural", "en-GB-RyanNeural", "en-GB-MaisieNeural", "en-GB-ThomasNeural",
            "en-AU-NatashaNeural", "en-AU-WilliamNeural", "en-AU-CarlyNeural", "en-AU-DarrenNeural",
            "en-CA-ClaraNeural", "en-CA-LiamNeural", "en-IN-NeerjaNeural", "en-IN-PrabhatNeural",
            "en-IE-EmilyNeural", "en-IE-ConnorNeural", "en-NZ-MollyNeural", "en-NZ-MitchellNeural",
            "en-ZA-LeahNeural", "en-ZA-LukeNeural", "en-SG-LunaNeural", "en-SG-WayneNeural"
        };

        private static readonly string[] VoiceLabels =
        {
            "Ava · US · F", "Andrew · US · M", "Jenny · US · F", "Guy · US · M",
            "Sonia · UK · F", "Ryan · UK · M", "Maisie · UK · F", "Thomas · UK · M",
            "Natasha · AU · F", "William · AU · M", "Carly · AU · F", "Darren · AU · M",
            "Clara · CA · F", "Liam · CA · M", "Neerja · IN · F", "Prabhat · IN · M",
            "Emily · IE · F", "Connor · IE · M", "Molly · NZ · F", "Mitchell · NZ · M",
            "Leah · ZA · F", "Luke · ZA · M", "Luna · SG · F", "Wayne · SG · M"
        };

        private static readonly string[] MediaFilters = { "ALL", "IN QUEUE", "OUT", "AUDIO", "VIDEO" };
        private static readonly string[] MediaSorts = { "A–Z", "NEWEST", "FOLDER", "QUEUE" };

        private static readonly string[] GuidedQuestions =
        {
            "What picture, mood, or story should the pizza communicate?",
            "Who is this pizza for, and what should make them smile?",
            "Choose the visual style: portrait, character, emblem, pattern, or abstract art.",
            "Name the three most important colors or ingredient families.",
            "What must be instantly recognizable from across the room?",
            "Choose a composition: centered, mirrored, radial, or deliberately freeform.",
            "Which ingredients are required, and which must be avoided?",
            "How bold should the detail be: clean, layered, or highly intricate?",
            "Describe the border, crust-ring, or background treatment.",
            "What expression, lettering, or small signature detail should it have?",
            "Should flavor, cost, or visual accuracy win when there is a tradeoff?",
            "What final surprise should the crew add without losing the main idea?",
            "How should contrasting light and dark ingredients separate the key features?",
            "Which repeated shapes should create rhythm around the pizza?",
            "Name one alternate ingredient the audition tool should compare.",
            "How should the design look after baking and slight ingredient movement?",
            "What should this version be named in the recipe book?",
            "Give the crew one final acceptance rule before it builds the pizza."
        };

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
        private GUIStyle mediaTrackButtonStyle;
        private GUIStyle mediaTrackActiveButtonStyle;
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
        private Texture2D connectionPulseTexture;
        private bool exportedThemeEvidenceRecorded;
        private bool exportedAnimationEvidenceRecorded;

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
            agentAudioSource = GetComponent<AudioSource>();
            if (agentAudioSource == null) agentAudioSource = gameObject.AddComponent<AudioSource>();
            agentAudioSource.playOnAwake = false;
            agentAudioSource.volume = agentVoiceVolume;
            RefreshMicrophones();
            GameObject mediaObject = new GameObject("Barros Media Deck");
            // Keep music active when the user switches away from the AI tab.
            // The sibling still dies cleanly with the owning Pizza Creator canvas.
            mediaObject.transform.SetParent(transform.parent, false);
            mediaDeck = mediaObject.AddComponent<MediaDeck>();
            mediaDeck.Configure(evidence, game);
            lastMusicInboxRevision = mediaDeck.InboxRevision();
            agentVoiceIndexes["Flavor Chef"] = 6;
            agentVoiceIndexes["Cost Manager"] = 11;
            agentVoiceIndexes["Customer Scout"] = 5;
            agentVoiceIndexes["Creative Director"] = 10;
            backend.Health(delegate(bool ready, string label, bool inputReady, bool speechReady)
            {
                backendReady = ready;
                backendLabel = ready ? label : "Backend unavailable";
                sttConfigured = inputReady;
                ttsConfigured = speechReady;
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

        private void OnDestroy()
        {
            if (recording) CancelVoiceRecording();
            StopAgentSpeech();
        }

        private void Update()
        {
            if (recording && Time.realtimeSinceStartup - recordingStarted >= 29.5f) StopVoiceAndTranscribe();
            if (mediaDeck != null && mediaDeck.AutoImport && !musicImportBusy && Time.realtimeSinceStartup >= nextMusicInboxCheck)
            {
                nextMusicInboxCheck = Time.realtimeSinceStartup + 5f;
                long revision = mediaDeck.InboxRevision();
                if (revision != 0 && revision != lastMusicInboxRevision)
                {
                    lastMusicInboxRevision = revision;
                    RefreshMusicLibrary();
                }
            }
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
            if (mode == DesignerMode.Media) return "media";
            return "chat";
        }

        private void OnGUI()
        {
            if (tab == null || !tab.isOn || panelRect == null) return;
            EnsureStyles();
            Rect screenRect = GetScreenRect(panelRect);
            if (screenRect.width < 200f || screenRect.height < 300f)
                screenRect = new Rect(Screen.width * 0.69f, 60f, Screen.width * 0.31f, Screen.height - 60f);
            screenRect = FitBesideTabRail(screenRect);
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

        private Rect FitBesideTabRail(Rect screenRect)
        {
            RectTransform activeTabRect = tab != null ? tab.transform as RectTransform : null;
            if (activeTabRect == null) return screenRect;
            Rect tabScreenRect = GetScreenRect(activeTabRect);
            if (tabScreenRect.width <= 1f || tabScreenRect.height <= 1f) return screenRect;

            float gap = Mathf.Max(6f, Screen.width * 0.003f);
            float desiredLeft = tabScreenRect.xMax + gap;
            float originalRight = screenRect.xMax;
            if (desiredLeft > screenRect.x && originalRight - desiredLeft >= 360f)
                screenRect.xMin = desiredLeft;

            if (!layoutEvidenceRecorded && evidence != null)
            {
                layoutEvidenceRecorded = true;
                evidence.Record(
                    "ui.panel_fitted",
                    "left=" + screenRect.xMin.ToString("0.0") +
                    "; right=" + screenRect.xMax.ToString("0.0") +
                    "; width=" + screenRect.width.ToString("0.0") +
                    "; tab_right=" + tabScreenRect.xMax.ToString("0.0") +
                    "; gap=" + (screenRect.xMin - tabScreenRect.xMax).ToString("0.0"));
            }
            return screenRect;
        }

        private void DrawPanel()
        {
            GUI.Box(new Rect(0f, 0f, VirtualWidth, VirtualHeight), GUIContent.none, panelStyle);
            GUI.Label(new Rect(18f, 10f, 410f, 38f), HeaderForMode(), titleStyle);
            DrawConnection(new Rect(438f, 14f, 180f, 28f));
            string[] labels = { "Chat", "AI Lab", "Crew", "Voice", "Media" };
            for (int i = 0; i < labels.Length; i++)
            {
                Rect modeRect = new Rect(16f + i * 121f, 55f, 114f, 39f);
                GUIStyle style = (int)mode == i ? activeButtonStyle : buttonStyle;
                if (GUI.Button(modeRect, labels[i], style)) SetMode((DesignerMode)i);
            }

            Rect content = mode == DesignerMode.Media ? new Rect(14f, 105f, 612f, 927f) : new Rect(14f, 105f, 612f, 755f);
            GUILayout.BeginArea(content);
            scroll = GUILayout.BeginScrollView(scroll, false, true);
            if (mode == DesignerMode.Chat) DrawChat();
            else if (mode == DesignerMode.Lab) DrawLab();
            else if (mode == DesignerMode.Crew) DrawCrew();
            else if (mode == DesignerMode.Voice) DrawVoice();
            else DrawMediaDeck();
            GUILayout.Space(12f);
            GUILayout.EndScrollView();
            GUILayout.EndArea();

            if (mode != DesignerMode.Media) DrawComposer(new Rect(14f, 868f, 612f, 168f));
        }

        private void DrawConnection(Rect rect)
        {
            GUI.Box(rect, GUIContent.none, cardStyle);
            Color old = GUI.color;
            GUI.color = Color.white;
            Rect indicatorRect = new Rect(rect.x + 7f, rect.y + 5f, 18f, 18f);
            if (backendReady && connectionPulseTexture != null)
            {
                const int frameCount = 8;
                int frame = Mathf.FloorToInt(Time.realtimeSinceStartup * 8f) % frameCount;
                GUI.DrawTextureWithTexCoords(indicatorRect, connectionPulseTexture,
                    new Rect(frame / (float)frameCount, 0f, 1f / frameCount, 1f));
                if (!exportedAnimationEvidenceRecorded && evidence != null)
                {
                    exportedAnimationEvidenceRecorded = true;
                    evidence.Record("ui.exported_animation_loaded", "name=connection-pulse;frames=8;fps=8;target=Unity2017");
                }
            }
            else
            {
                GUI.DrawTexture(new Rect(rect.x + 9f, rect.y + 8f, 12f, 12f), backendReady ? greenTexture : amberTexture);
            }
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
            if (mode == DesignerMode.Media) return "Barro's Media Deck";
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
            string[] actions = { "Build with me", "Pizza art", "Surprise me", "Improve this" };
            for (int row = 0; row < 2; row++)
            {
                GUILayout.BeginHorizontal();
                for (int column = 0; column < 2; column++)
                {
                    int i = row * 2 + column;
                    GUIStyle style = chatAction == actions[i] ? activeButtonStyle : buttonStyle;
                    if (GUILayout.Button(actions[i], style, GUILayout.Height(34f))) chatAction = actions[i];
                }
                GUILayout.EndHorizontal();
            }
            GUILayout.Space(8f);
            if (chatAction == "Build with me") DrawGuidedSession();
            if (chatAction == "Pizza art") DrawArtStudio();
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
                GUILayout.Box("Try either kind of creation:\n\n“Use chicken, bacon and jalapeno; keep it profitable.”\n\n“Make a detailed Santa Claus pizza picture.”\n\nPizza Art converts colors and shapes into precise native ingredient placements.", cardStyle, GUILayout.ExpandWidth(true), GUILayout.MinHeight(170f));
            }
        }

        private void DrawGuidedSession()
        {
            GUILayout.BeginVertical(cardStyle);
            GUILayout.BeginHorizontal();
            GUILayout.Label("Guided Pizza Session", subtitleStyle);
            GUILayout.FlexibleSpace();
            GUILayout.Label(guidedActive ? "STEP " + (guidedStep + 1) + " / " + guidedStepCount : "choose a journey", smallStyle, GUILayout.Width(96f));
            GUILayout.EndHorizontal();
            GUILayout.Label("The crew asks one useful question at a time, then turns your answers into a build-ready design brief.", smallStyle);
            GUILayout.BeginHorizontal();
            int[] stepOptions = { 6, 8, 12, 18 };
            for (int i = 0; i < stepOptions.Length; i++)
                if (GUILayout.Button(stepOptions[i] + " steps", guidedStepCount == stepOptions[i] ? activeButtonStyle : buttonStyle, GUILayout.Height(31f)))
                    guidedStepCount = stepOptions[i];
            GUILayout.EndHorizontal();
            GUILayout.BeginHorizontal();
            string[] tones = { "Professional", "Playful", "Goofball" };
            for (int i = 0; i < tones.Length; i++)
                if (GUILayout.Button(tones[i], guidedTone == tones[i] ? activeButtonStyle : buttonStyle, GUILayout.Height(31f))) guidedTone = tones[i];
            GUILayout.EndHorizontal();
            if (!guidedActive)
            {
                if (GUILayout.Button("START GUIDED BUILD", primaryButtonStyle, GUILayout.Height(43f))) StartGuidedSession();
            }
            else
            {
                GUILayout.Label(GuidedQuestions[Mathf.Clamp(guidedStep, 0, GuidedQuestions.Length - 1)], bodyStyle);
                GUILayout.Label("Type your answer below and press ADD STEP.", smallStyle);
                if (GUILayout.Button("CANCEL SESSION", buttonStyle, GUILayout.Height(30f))) CancelGuidedSession();
            }
            GUILayout.EndVertical();
            GUILayout.Space(7f);
        }

        private void DrawArtStudio()
        {
            GUILayout.BeginVertical(cardStyle);
            GUILayout.BeginHorizontal();
            GUILayout.Label("Pizza Art Studio", subtitleStyle, GUILayout.Width(255f));
            GUILayout.FlexibleSpace();
            GUILayout.Label("up to 180 real pieces", smallStyle);
            GUILayout.EndHorizontal();
            GUILayout.Label("Pick a starting subject, then describe colors, expression or changes in the message box.", smallStyle);

            string[] templates = { "Santa", "Face", "Heart", "Tree", "Smiley", "Snowman", "Star" };
            for (int row = 0; row < 2; row++)
            {
                GUILayout.BeginHorizontal();
                int start = row == 0 ? 0 : 4;
                int end = row == 0 ? 4 : templates.Length;
                for (int i = start; i < end; i++)
                {
                    GUIStyle style = artTemplate == templates[i] ? activeButtonStyle : buttonStyle;
                    if (GUILayout.Button(templates[i], style, GUILayout.Height(31f))) SelectArtTemplate(templates[i]);
                }
                if (row == 1) GUILayout.FlexibleSpace();
                GUILayout.EndHorizontal();
            }

            GUILayout.Label("Detail", smallStyle);
            GUILayout.BeginHorizontal();
            string[] details = { "Draft", "Standard", "High" };
            for (int i = 0; i < details.Length; i++)
                if (GUILayout.Button(details[i], artDetail == details[i] ? activeButtonStyle : buttonStyle, GUILayout.Height(31f))) artDetail = details[i];
            GUILayout.EndHorizontal();

            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Style: " + artStyle, activeButtonStyle, GUILayout.Height(31f)))
            {
                artStyle = artStyle == "Precision" ? "Organic" : "Precision";
                status = "Pizza Art style set to " + artStyle + ".";
            }
            if (GUILayout.Button("Palette: " + artPalette, artPalette == "Vegan" ? activeButtonStyle : buttonStyle, GUILayout.Height(31f)))
            {
                artPalette = artPalette == "Classic" ? "Vegan" : "Classic";
                status = "Pizza Art palette set to " + artPalette + ".";
            }
            GUILayout.EndHorizontal();
            GUILayout.Label("Symmetry Studio", smallStyle);
            GUILayout.BeginHorizontal();
            string[] symmetryModes = { "Freeform", "Mirror", "Radial" };
            for (int i = 0; i < symmetryModes.Length; i++)
                if (GUILayout.Button(symmetryModes[i], artSymmetry == symmetryModes[i] ? activeButtonStyle : buttonStyle, GUILayout.Height(31f)))
                {
                    artSymmetry = symmetryModes[i];
                    status = artSymmetry + " composition selected.";
                }
            GUILayout.EndHorizontal();
            GUILayout.EndVertical();
            GUILayout.Space(7f);
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
            if (GUILayout.Button("SURPRISE ME — GENERATE 3", primaryButtonStyle, GUILayout.Height(52f)))
            {
                if (string.IsNullOrEmpty(prompt)) prompt = "Create three distinctive crowd-pleasing pizzas.";
                Submit("/lab", 3);
            }
            GUILayout.EndVertical();
            GUILayout.Space(8f);
            if (recipes.Count == 0)
            {
                GUILayout.Box("Three valid alternatives will appear here with taste, cost, profit, popularity, novelty and native preview controls.", cardStyle, GUILayout.MinHeight(82f));
                GUILayout.Space(7f);
                GUILayout.BeginVertical(cardStyle);
                GUILayout.Label("Creative shortcuts", subtitleStyle);
                GUILayout.Label("Start with an ingredient picture, ask the four-agent crew, or build the idea one guided choice at a time.", smallStyle);
                GUILayout.BeginHorizontal();
                if (GUILayout.Button("OPEN ART STUDIO", buttonStyle, GUILayout.Height(38f)))
                {
                    chatAction = "Pizza art";
                    mode = DesignerMode.Chat;
                    status = "Pizza Art Studio opened with Symmetry Studio and precision placement.";
                }
                if (GUILayout.Button("ASK DESIGN CREW", buttonStyle, GUILayout.Height(38f))) mode = DesignerMode.Crew;
                if (GUILayout.Button("GUIDED BUILD", activeButtonStyle, GUILayout.Height(38f)))
                {
                    chatAction = "Build with me";
                    mode = DesignerMode.Chat;
                }
                GUILayout.EndHorizontal();
                GUILayout.EndVertical();
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
                if (GUILayout.Button("Generate 3 more", buttonStyle, GUILayout.Height(38f))) Submit("/lab", 3);
                GUILayout.EndVertical();
            }
        }

        private void DrawLabCandidate(AiRecipe recipe, int index)
        {
            GUILayout.BeginVertical(index == selectedRecipe ? cardStyle : panelStyle);
            GUILayout.BeginHorizontal();
            GUILayout.Label(recipe.Name, subtitleStyle);
            GUILayout.FlexibleSpace();
            if (GUILayout.Button("Preview", buttonStyle, GUILayout.Width(104f), GUILayout.Height(34f))) Preview(recipe, index);
            if (GUILayout.Button("Use", primaryButtonStyle, GUILayout.Width(90f), GUILayout.Height(34f))) Apply(recipe, index);
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
            DrawCrewVoiceControls();
            if (agents.Count == 0)
            {
                GUILayout.BeginVertical(cardStyle);
                GUILayout.Label("4 agents ready", subtitleStyle);
                DrawAgentReady("Flavor Chef", "Suggesting bold, craveable combinations.", false);
                DrawAgentReady("Cost Manager", "Keeping ingredients efficient.", false);
                DrawAgentReady("Customer Scout", "Tracking broad preferences.", false);
                DrawAgentReady("Creative Director", "Ensuring a unique signature.", false);
                if (GUILayout.Button("ASK ALL FOUR AGENTS", primaryButtonStyle, GUILayout.Height(48f)))
                {
                    crewFocusAgent = "";
                    Submit("/crew", 1);
                }
                GUILayout.EndVertical();
                return;
            }
            for (int i = 0; i < agents.Count; i++) DrawAgentReady(agents[i].Agent, agents[i].Message, true);
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
            if (recipes.Count > 0)
            {
                if (GUILayout.Button(agentSpeechBusy ? "ROUNDTABLE · " + currentSpeakingAgent + " · " + agentSpeechQueue.Count + " WAITING" : "PLAY AGENT ROUNDTABLE", activeButtonStyle, GUILayout.Height(39f)))
                    QueueAgentRoundtable();
                GUILayout.BeginHorizontal();
                if (GUILayout.Button("Balanced", buttonStyle, GUILayout.Height(35f))) ApplyCrewPreset("balanced");
                if (GUILayout.Button("Max flavor", activeButtonStyle, GUILayout.Height(35f))) ApplyCrewPreset("flavor");
                if (GUILayout.Button("Max profit", buttonStyle, GUILayout.Height(35f))) ApplyCrewPreset("profit");
                GUILayout.EndHorizontal();
                if (GUILayout.Button("APPLY CREW RECIPE", primaryButtonStyle, GUILayout.Height(52f))) Apply(recipes[0], 0);
            }
        }

        private void DrawCrewVoiceControls()
        {
            GUILayout.BeginVertical(cardStyle);
            GUILayout.BeginHorizontal();
            GUILayout.Label("Agent voices", subtitleStyle);
            GUILayout.FlexibleSpace();
            string voiceLabel = !ttsConfigured ? "SETUP NEEDED" : (agentVoicesMuted ? "MUTED" : "ON");
            if (GUILayout.Button(voiceLabel, !agentVoicesMuted && ttsConfigured ? activeButtonStyle : buttonStyle, GUILayout.Width(125f), GUILayout.Height(32f)))
            {
                if (!ttsConfigured)
                    status = "Azure agent voices are not configured. Open CONFIGURE_AI_PROVIDER.ps1 and add the Speech region and key environment name.";
                else
                {
                    agentVoicesMuted = !agentVoicesMuted;
                    if (agentVoicesMuted) StopAgentSpeech();
                    status = agentVoicesMuted ? "Agent voices muted." : "Agent voices on. New focused replies will speak automatically.";
                }
            }
            if (GUILayout.Button("VOICE CHECK", buttonStyle, GUILayout.Width(102f), GUILayout.Height(32f))) QueueVoiceCheck();
            if (GUILayout.Button("STOP", buttonStyle, GUILayout.Width(72f), GUILayout.Height(32f))) StopAgentSpeech();
            GUILayout.EndHorizontal();
            GUILayout.Label("24 selectable English Azure voices: 12 feminine and 12 masculine across US, UK, AU, CA, IN, IE, NZ, ZA and SG. Speech starts muted and never reads links, code or file paths.", smallStyle);
            GUILayout.BeginHorizontal();
            GUILayout.Label("Voice", smallStyle, GUILayout.Width(52f));
            agentVoiceVolume = GUILayout.HorizontalSlider(agentVoiceVolume, 0f, 1f, GUILayout.Width(130f));
            if (agentAudioSource != null) agentAudioSource.volume = agentVoiceVolume;
            if (GUILayout.Button("Rate " + agentSpeechRate.ToString("0.0") + "×", buttonStyle, GUILayout.Width(92f), GUILayout.Height(29f)))
                agentSpeechRate = agentSpeechRate >= 1.1f ? 0.9f : agentSpeechRate + 0.1f;
            if (GUILayout.Button("Gap " + agentSpeechGap.ToString("0.00") + "s", buttonStyle, GUILayout.Width(94f), GUILayout.Height(29f)))
                agentSpeechGap = agentSpeechGap >= 0.75f ? 0.25f : agentSpeechGap + 0.25f;
            GUILayout.EndHorizontal();
            if (agentSpeechBusy) GUILayout.Label("Now speaking: " + currentSpeakingAgent + " · " + agentSpeechQueue.Count + " voice turn" + (agentSpeechQueue.Count == 1 ? "" : "s") + " queued · music stays paused until everyone finishes.", speakerStyle);
            else GUILayout.Label(ttsConfigured ? "Ready for a focused reply or an orderly four-agent roundtable." : "Run provider setup to enable audible agent replies.", smallStyle);
            GUILayout.EndVertical();
            GUILayout.Space(6f);
        }

        private void DrawAgentReady(string name, string detail, bool hasFeedback)
        {
            GUILayout.BeginVertical(cardStyle);
            GUILayout.BeginHorizontal();
            GUILayout.Label(name, speakerStyle);
            GUILayout.FlexibleSpace();
            if (GUILayout.Button(AgentVoiceLabel(name), buttonStyle, GUILayout.Width(132f), GUILayout.Height(29f))) CycleAgentVoice(name);
            if (GUILayout.Button("ASK", buttonStyle, GUILayout.Width(58f), GUILayout.Height(29f))) FocusAgent(name);
            bool previousEnabled = GUI.enabled;
            GUI.enabled = previousEnabled && hasFeedback;
            if (GUILayout.Button(agentSpeechBusy ? "QUEUE" : "SPEAK", buttonStyle, GUILayout.Width(68f), GUILayout.Height(29f))) SpeakAgent(name, detail);
            GUI.enabled = previousEnabled;
            GUILayout.EndHorizontal();
            GUILayout.Label(detail, smallStyle);
            GUILayout.EndVertical();
            GUILayout.Space(3f);
        }

        private void DrawVoice()
        {
            bool microphoneAvailable = HasMicrophone();
            float liveLevel = CurrentMicrophoneLevel();
            GUILayout.BeginVertical(cardStyle);
            GUILayout.BeginHorizontal();
            GUILayout.Label("Chef Voice", titleStyle);
            GUILayout.FlexibleSpace();
            string readiness = recording ? "● LISTENING" : (!microphoneAvailable ? "NO MICROPHONE" : (!sttConfigured ? "SETUP NEEDED" : "READY"));
            GUILayout.Label(readiness, recording || !microphoneAvailable || !sttConfigured ? speakerStyle : smallStyle, GUILayout.Width(145f));
            GUILayout.EndHorizontal();
            GUILayout.Label("Talk naturally, review the transcript, then hear the Designer or full Crew answer without overlapping the soundtrack.", smallStyle);

            GUILayout.Space(5f);
            GUILayout.Label("Conversation partner", subtitleStyle);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("PIZZA DESIGNER", !voiceUseCrew ? activeButtonStyle : buttonStyle, GUILayout.Height(35f)))
            {
                voiceUseCrew = false;
                status = "Voice questions will receive one concise Creative Director reply.";
            }
            if (GUILayout.Button("FULL DESIGN CREW", voiceUseCrew ? activeButtonStyle : buttonStyle, GUILayout.Height(35f)))
            {
                voiceUseCrew = true;
                status = "Voice questions will receive four orderly specialist replies.";
            }
            GUILayout.EndHorizontal();
            GUILayout.BeginHorizontal();
            GUILayout.Label(voiceUseCrew ? "Four perspectives · one speaker at a time" : "One focused answer · fastest response", smallStyle);
            GUILayout.FlexibleSpace();
            if (GUILayout.Button(voiceAutoContinue ? "AUTO LISTEN ON" : "AUTO LISTEN OFF", voiceAutoContinue ? activeButtonStyle : buttonStyle, GUILayout.Width(145f), GUILayout.Height(31f)))
            {
                voiceAutoContinue = !voiceAutoContinue;
                status = voiceAutoContinue
                    ? "After spoken replies finish, Chef Voice will listen for the next turn."
                    : "Automatic follow-up listening is off; press Start listening for each turn.";
            }
            GUILayout.EndHorizontal();

            GUILayout.Space(7f);
            GUILayout.Label("Microphone", subtitleStyle);
            GUILayout.BeginHorizontal();
            GUILayout.Label("Input", smallStyle, GUILayout.Width(48f));
            string deviceLabel = microphoneAvailable ? SelectedMicrophoneLabel() : "No Windows microphone";
            GUI.enabled = !recording;
            if (GUILayout.Button(deviceLabel, buttonStyle, GUILayout.Height(31f))) CycleMicrophone();
            if (GUILayout.Button("REFRESH", buttonStyle, GUILayout.Width(82f), GUILayout.Height(31f))) RefreshMicrophones();
            GUI.enabled = true;
            if (GUILayout.Button(microphoneMuted ? "MUTED" : "LIVE", microphoneMuted ? buttonStyle : activeButtonStyle, GUILayout.Width(72f), GUILayout.Height(31f)))
            {
                microphoneMuted = !microphoneMuted;
                if (microphoneMuted && recording) CancelVoiceRecording();
                status = microphoneMuted ? "Microphone muted." : "Microphone ready when a Windows input is connected.";
            }
            GUILayout.EndHorizontal();
            GUILayout.BeginHorizontal();
            GUILayout.Label("Input gain", smallStyle, GUILayout.Width(78f));
            microphoneGain = GUILayout.HorizontalSlider(microphoneGain, 0.5f, 2f, GUILayout.Width(330f));
            GUILayout.Label(microphoneGain.ToString("0.0") + "×", smallStyle, GUILayout.Width(54f));
            GUILayout.FlexibleSpace();
            GUILayout.Label(VoiceSignalLabel(liveLevel), recording ? speakerStyle : smallStyle, GUILayout.Width(94f));
            GUILayout.EndHorizontal();
            Rect waveRect = GUILayoutUtility.GetRect(560f, 112f, GUILayout.ExpandWidth(true));
            DrawWaveform(waveRect);
            string micLabel = recording ? "STOP & TRANSCRIBE" : (microphoneMuted ? "MICROPHONE MUTED" : (!microphoneAvailable ? "RETRY MICROPHONE" : (!sttConfigured ? "VOICE INPUT SETUP NEEDED" : "START LISTENING")));
            GUI.enabled = recording || (!microphoneMuted && (microphoneAvailable ? sttConfigured : true));
            if (GUILayout.Button(micLabel, recording ? activeButtonStyle : primaryButtonStyle, GUILayout.Height(52f)))
            {
                if (recording) StopVoiceAndTranscribe(); else StartVoice();
            }
            GUI.enabled = true;
            if (!sttConfigured) GUILayout.Label("Azure voice input is not configured. Run the provider setup and select Azure Speech before recording.", speakerStyle);
            else if (!ttsConfigured) GUILayout.Label("Transcription is ready, but spoken agent replies still need Azure agent voices enabled.", speakerStyle);
            else GUILayout.Label("Voice input and agent speech are configured. Voices remain muted until enabled in Design Crew.", smallStyle);
            GUILayout.EndVertical();
            GUILayout.Space(6f);
            if (!string.IsNullOrEmpty(transcript))
            {
                GUILayout.BeginVertical(cardStyle);
                GUILayout.BeginHorizontal();
                GUILayout.Label("Latest transcript", speakerStyle);
                GUILayout.FlexibleSpace();
                if (GUILayout.Button("ASK AGAIN", buttonStyle, GUILayout.Width(92f), GUILayout.Height(28f)))
                {
                    prompt = transcript;
                    promptFromVoice = true;
                    Submit(voiceUseCrew ? "/crew" : "/chat", 1);
                }
                if (GUILayout.Button("CLEAR", buttonStyle, GUILayout.Width(64f), GUILayout.Height(28f))) transcript = "";
                GUILayout.EndHorizontal();
                GUILayout.Label(transcript, bodyStyle);
                GUILayout.EndVertical();
            }
            if (!string.IsNullOrEmpty(pendingVoiceError)) GUILayout.Label(pendingVoiceError, speakerStyle);
            GUILayout.BeginVertical(cardStyle);
            GUILayout.Label("Quick voice preferences", subtitleStyle);
            GUILayout.BeginHorizontal();
            GUILayout.Label("Heat", smallStyle, GUILayout.Width(48f));
            string[] heats = { "Mild", "Medium", "Hot" };
            for (int i = 0; i < heats.Length; i++)
            {
                if (GUILayout.Button(heats[i], heat == heats[i] ? activeButtonStyle : buttonStyle, GUILayout.Height(36f))) heat = heats[i];
            }
            GUILayout.EndHorizontal();
            GUILayout.EndVertical();
            if (recipes.Count > 0) DrawRecipeCard(recipes[0], true, true);
        }

        private static string VoiceSignalLabel(float level)
        {
            if (level <= 0.01f) return "Signal —";
            if (level < 0.16f) return "Signal low";
            if (level > 0.88f) return "Signal hot";
            return "Signal good";
        }

        private void DrawMediaDeck()
        {
            if (mediaDeck == null)
            {
                GUILayout.Box("Media Deck is unavailable in this session.", cardStyle, GUILayout.MinHeight(150f));
                return;
            }
            GUILayout.BeginVertical(cardStyle);
            GUILayout.Label("Barro's Music Player", titleStyle);
            GUILayout.BeginHorizontal();
            GUILayout.Label("Soundtrack", smallStyle, GUILayout.Width(96f));
            if (GUILayout.Button("BARRO'S", mediaDeck.BarrosReplacesStock ? activeButtonStyle : buttonStyle, GUILayout.Height(32f))) mediaDeck.PlayBarrosPlaylist();
            if (GUILayout.Button("STOCK", !mediaDeck.BarrosReplacesStock ? activeButtonStyle : buttonStyle, GUILayout.Height(32f))) mediaDeck.PlayStockMusic();
            GUILayout.EndHorizontal();
            GUILayout.Label(mediaDeck.BarrosReplacesStock ? "Exclusive mode · Barro's ON · Stock OFF" : "Exclusive mode · Stock ON · Barro's OFF", smallStyle);
            GUILayout.BeginHorizontal();
            GUILayout.Label("Music library", smallStyle, GUILayout.Width(96f));
            if (GUILayout.Button(musicImportBusy ? "IMPORTING…" : "IMPORT + REFRESH", buttonStyle, GUILayout.Height(31f))) RefreshMusicLibrary();
            if (GUILayout.Button("OPEN FOLDER", buttonStyle, GUILayout.Width(108f), GUILayout.Height(31f)))
            {
                try { System.Diagnostics.Process.Start(mediaDeck.ImportFolder); }
                catch (Exception exception) { status = "Could not open music inbox: " + exception.Message; }
            }
            if (GUILayout.Button("REPORT", buttonStyle, GUILayout.Width(78f), GUILayout.Height(31f)))
            {
                try
                {
                    if (File.Exists(mediaDeck.ConversionReportFile)) System.Diagnostics.Process.Start(mediaDeck.ConversionReportFile);
                    else status = "No conversion report exists yet. Import or refresh music first.";
                }
                catch (Exception exception) { status = "Could not open conversion report: " + exception.Message; }
            }
            GUILayout.EndHorizontal();
            GUILayout.Label(mediaDeck.CurrentTitle, speakerStyle);
            if (mediaDeck.BarrosReplacesStock && mediaDeck.CurrentIndex >= 0)
                GUILayout.Label("Now playing · file " + (mediaDeck.CurrentIndex + 1) + " of " + mediaDeck.Tracks.Count + "   |   Up next · " + mediaDeck.NextTitle, smallStyle);
            GUILayout.Label(mediaDeck.ActivePlaylistName + " · " + mediaDeck.PlaylistCount + " of " + mediaDeck.Tracks.Count + " library files · " + mediaDeck.NamedPlaylistCount + " saved mix" + (mediaDeck.NamedPlaylistCount == 1 ? "" : "es"), smallStyle);
            GUILayout.Label(mediaDeck.Status, smallStyle);
            GUILayout.Label("Drop MP3, WAV, or OGG into the folder. Import + Refresh creates playable OGG copies; MP4 lyric videos also appear here.", smallStyle);

            if (mediaDeck.CurrentIsVideo)
            {
                GUILayout.BeginHorizontal();
                GUILayout.Label("LYRIC VIDEO · " + (mediaDeck.VideoPlaying ? "PLAYING" : mediaDeck.ShowingVideo ? "PAUSED" : "PREPARING"), subtitleStyle);
                GUILayout.FlexibleSpace();
                if (GUILayout.Button(mediaDeck.LyricsVisible ? "LYRICS ON" : "LYRICS OFF", mediaDeck.LyricsVisible ? activeButtonStyle : buttonStyle, GUILayout.Width(96f), GUILayout.Height(28f)))
                    mediaDeck.LyricsVisible = !mediaDeck.LyricsVisible;
                if (GUILayout.Button(mediaVideoExpanded ? "COMPACT" : "EXPAND", buttonStyle, GUILayout.Width(92f), GUILayout.Height(28f)))
                    mediaVideoExpanded = !mediaVideoExpanded;
                GUILayout.EndHorizontal();
                float videoHeight = mediaVideoExpanded ? (mediaDeck.VideoAspect < 1f ? 520f : 330f) : 230f;
                Rect videoRect = GUILayoutUtility.GetRect(560f, videoHeight, GUILayout.ExpandWidth(true));
                GUI.Box(videoRect, GUIContent.none, panelStyle);
                Rect fittedRect = new Rect(videoRect.x + 8f, videoRect.y + 8f, videoRect.width - 16f, videoRect.height - 16f);
                if (!mediaDeck.LyricsVisible)
                    GUI.Label(fittedRect, "Lyrics hidden · audio keeps playing from the same position", subtitleStyle);
                else if (mediaDeck.ShowingVideo && mediaDeck.VideoTexture != null)
                    GUI.DrawTexture(fittedRect, mediaDeck.VideoTexture, ScaleMode.ScaleToFit, false);
                else
                    GUI.Label(fittedRect, "Preparing lyric video…", subtitleStyle);
            }
            else
            {
                Rect waveRect = GUILayoutUtility.GetRect(560f, 118f, GUILayout.ExpandWidth(true));
                DrawMediaWaveform(waveRect, mediaDeck.GetWaveform(52));
                GUILayout.BeginHorizontal();
                GUILayout.Label(mediaDeck.TimedLyricsAvailable ? "TIMED LYRICS" : "LYRICS", subtitleStyle);
                GUILayout.FlexibleSpace();
                if (GUILayout.Button(mediaDeck.LyricsVisible ? "LYRICS ON" : "LYRICS OFF", mediaDeck.LyricsVisible ? activeButtonStyle : buttonStyle, GUILayout.Width(96f), GUILayout.Height(28f)))
                    mediaDeck.LyricsVisible = !mediaDeck.LyricsVisible;
                GUILayout.EndHorizontal();
                if (mediaDeck.LyricsVisible && mediaDeck.TimedLyricsAvailable)
                {
                    GUILayout.BeginVertical(panelStyle);
                    if (!string.IsNullOrEmpty(mediaDeck.PreviousLyric)) GUILayout.Label(mediaDeck.PreviousLyric, smallStyle);
                    GUILayout.Label(string.IsNullOrEmpty(mediaDeck.CurrentLyric) ? "Instrumental intro…" : "▶  " + mediaDeck.CurrentLyric, speakerStyle);
                    if (!string.IsNullOrEmpty(mediaDeck.NextLyric)) GUILayout.Label(mediaDeck.NextLyric, smallStyle);
                    GUILayout.EndVertical();
                }
                else if (mediaDeck.LyricsVisible && mediaDeck.CurrentIndex >= 0)
                    GUILayout.Label("No timed lyrics yet · add a same-name .lrc file beside this song to enable line highlighting.", smallStyle);
            }

            float progress = GUILayout.HorizontalSlider(mediaDeck.Progress, 0f, 1f, GUILayout.Height(24f));
            if (Mathf.Abs(progress - mediaDeck.Progress) > 0.002f) mediaDeck.Progress = progress;
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("◀", buttonStyle, GUILayout.Width(64f), GUILayout.Height(41f))) mediaDeck.Previous();
            if (GUILayout.Button(mediaDeck.IsPlaying ? "PAUSE" : "PLAY", primaryButtonStyle, GUILayout.Height(41f))) mediaDeck.TogglePlay();
            if (GUILayout.Button("STOP", buttonStyle, GUILayout.Width(76f), GUILayout.Height(41f))) mediaDeck.StopPlayback();
            if (GUILayout.Button("▶", buttonStyle, GUILayout.Width(64f), GUILayout.Height(41f))) mediaDeck.Next();
            GUILayout.EndHorizontal();
            GUILayout.BeginHorizontal();
            mediaDeck.Shuffle = GUILayout.Toggle(mediaDeck.Shuffle, " Shuffle", GUILayout.Width(110f));
            mediaDeck.Repeat = GUILayout.Toggle(mediaDeck.Repeat, " Repeat", GUILayout.Width(105f));
            mediaDeck.AutoImport = GUILayout.Toggle(mediaDeck.AutoImport, " Auto import", GUILayout.Width(125f));
            GUILayout.Label("Volume", smallStyle, GUILayout.Width(62f));
            mediaDeck.Volume = GUILayout.HorizontalSlider(mediaDeck.Volume, 0f, 1f, GUILayout.Width(130f));
            GUILayout.EndHorizontal();
            GUILayout.Label("Three-band tone · safe native mixer", subtitleStyle);
            mediaDeck.BassDb = DrawEqSlider("Bass", mediaDeck.BassDb);
            mediaDeck.MidDb = DrawEqSlider("Mid", mediaDeck.MidDb);
            mediaDeck.TrebleDb = DrawEqSlider("Treble", mediaDeck.TrebleDb);
            GUILayout.Label("Named playlists · the active mix becomes the startup queue", subtitleStyle);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("◀", buttonStyle, GUILayout.Width(46f), GUILayout.Height(32f))) { mediaDeck.CyclePlaylist(-1); playlistDeleteArmed = ""; }
            GUILayout.Label(mediaDeck.ActivePlaylistName, speakerStyle, GUILayout.Width(310f));
            if (GUILayout.Button("▶", buttonStyle, GUILayout.Width(46f), GUILayout.Height(32f))) { mediaDeck.CyclePlaylist(1); playlistDeleteArmed = ""; }
            GUILayout.Label(mediaDeck.PlaylistCount + " songs", smallStyle);
            GUILayout.EndHorizontal();
            playlistNameDraft = GUILayout.TextField(playlistNameDraft, inputStyle, GUILayout.Height(34f));
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("NEW", buttonStyle, GUILayout.Height(31f))) { mediaDeck.CreatePlaylist(playlistNameDraft); playlistNameDraft = ""; playlistDeleteArmed = ""; }
            if (GUILayout.Button("DUPLICATE", buttonStyle, GUILayout.Height(31f))) { mediaDeck.DuplicatePlaylist(playlistNameDraft); playlistNameDraft = ""; playlistDeleteArmed = ""; }
            if (GUILayout.Button("RENAME", buttonStyle, GUILayout.Height(31f))) { mediaDeck.RenamePlaylist(playlistNameDraft); playlistNameDraft = ""; playlistDeleteArmed = ""; }
            string deleteLabel = playlistDeleteArmed == mediaDeck.ActivePlaylistName ? "CONFIRM REMOVE" : "REMOVE MIX";
            if (GUILayout.Button(deleteLabel, buttonStyle, GUILayout.Height(31f)))
            {
                if (playlistDeleteArmed == mediaDeck.ActivePlaylistName) { mediaDeck.DeletePlaylist(); playlistDeleteArmed = ""; }
                else { playlistDeleteArmed = mediaDeck.ActivePlaylistName; status = "Press Confirm remove to remove the playlist. Music files will not be deleted."; }
            }
            GUILayout.EndHorizontal();
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("SAVE PLAYLISTS", activeButtonStyle, GUILayout.Height(32f))) mediaDeck.SavePlaylist();
            if (GUILayout.Button("RELOAD SAVED", buttonStyle, GUILayout.Height(32f))) mediaDeck.LoadPlaylist();
            if (GUILayout.Button("SELECT ALL", buttonStyle, GUILayout.Height(32f))) mediaDeck.SelectAll();
            if (GUILayout.Button("CLEAR", buttonStyle, GUILayout.Width(86f), GUILayout.Height(32f))) mediaDeck.ClearPlaylist();
            GUILayout.EndHorizontal();
            GUILayout.EndVertical();
            GUILayout.Space(7f);

            GUILayout.BeginVertical(cardStyle);
            GUILayout.Label("Music library · search, organize, and build the active mix", subtitleStyle);
            GUILayout.BeginHorizontal();
            mediaSearch = GUILayout.TextField(mediaSearch, inputStyle, GUILayout.Height(34f));
            if (GUILayout.Button(MediaFilters[mediaFilterMode], buttonStyle, GUILayout.Width(98f), GUILayout.Height(34f))) mediaFilterMode = (mediaFilterMode + 1) % MediaFilters.Length;
            if (GUILayout.Button(MediaSorts[mediaSortMode], buttonStyle, GUILayout.Width(82f), GUILayout.Height(34f))) mediaSortMode = (mediaSortMode + 1) % MediaSorts.Length;
            GUILayout.EndHorizontal();
            List<int> visibleTracks = VisibleMediaTracks();
            GUILayout.BeginHorizontal();
            GUILayout.Label(visibleTracks.Count + " shown · " + mediaDeck.Tracks.Count + " total · folders and duplicate filenames supported", smallStyle);
            GUILayout.FlexibleSpace();
            if (GUILayout.Button("ADD", buttonStyle, GUILayout.Width(64f), GUILayout.Height(29f))) mediaDeck.AddVisible(visibleTracks);
            if (GUILayout.Button("REMOVE", buttonStyle, GUILayout.Width(78f), GUILayout.Height(29f))) mediaDeck.RemoveVisible(visibleTracks);
            GUILayout.EndHorizontal();
            mediaLibraryScroll = GUILayout.BeginScrollView(
                mediaLibraryScroll,
                false,
                true,
                GUI.skin.horizontalScrollbar,
                GUI.skin.verticalScrollbar,
                panelStyle,
                GUILayout.Height(340f));
            for (int visible = 0; visible < visibleTracks.Count; visible++)
            {
                int i = visibleTracks[visible];
                MediaTrack track = mediaDeck.Tracks[i];
                int queuePosition = mediaDeck.QueuePosition(i);
                string label = track.Title + (track.IsVideo ? "  [LYRIC VIDEO]" : "  [" + track.Extension + "]") + "\n" + track.Folder;
                GUILayout.BeginHorizontal();
                GUIStyle trackStyle = mediaDeck.BarrosReplacesStock && i == mediaDeck.CurrentIndex ? mediaTrackActiveButtonStyle : mediaTrackButtonStyle;
                if (GUILayout.Button(label, trackStyle, GUILayout.Width(360f), GUILayout.Height(56f))) mediaDeck.Select(i);
                if (GUILayout.Button(queuePosition >= 0 ? "IN · " + (queuePosition + 1) : "OUT", queuePosition >= 0 ? activeButtonStyle : buttonStyle, GUILayout.Width(68f), GUILayout.Height(56f))) mediaDeck.ToggleQueued(i);
                GUI.enabled = queuePosition > 0;
                if (GUILayout.Button("↑", buttonStyle, GUILayout.Width(34f), GUILayout.Height(56f))) mediaDeck.MoveQueued(i, -1);
                GUI.enabled = queuePosition >= 0 && queuePosition < mediaDeck.PlaylistCount - 1;
                if (GUILayout.Button("↓", buttonStyle, GUILayout.Width(34f), GUILayout.Height(56f))) mediaDeck.MoveQueued(i, 1);
                GUI.enabled = true;
                GUILayout.EndHorizontal();
            }
            if (mediaDeck.Tracks.Count == 0) GUILayout.Label("Add project-owned files to BarrosAI/assets/music and press Refresh.", bodyStyle);
            else if (visibleTracks.Count == 0) GUILayout.Label("No songs match this search and filter. Clear the search or cycle the filter.", bodyStyle);
            GUILayout.Space(10f);
            GUILayout.EndScrollView();
            GUILayout.EndVertical();
        }

        private List<int> VisibleMediaTracks()
        {
            List<int> result = new List<int>();
            if (mediaDeck == null) return result;
            string query = (mediaSearch ?? "").Trim();
            for (int i = 0; i < mediaDeck.Tracks.Count; i++)
            {
                MediaTrack track = mediaDeck.Tracks[i];
                bool queued = mediaDeck.IsQueued(i);
                if (mediaFilterMode == 1 && !queued) continue;
                if (mediaFilterMode == 2 && queued) continue;
                if (mediaFilterMode == 3 && track.IsVideo) continue;
                if (mediaFilterMode == 4 && !track.IsVideo) continue;
                if (!string.IsNullOrEmpty(query)
                    && track.Title.IndexOf(query, StringComparison.OrdinalIgnoreCase) < 0
                    && track.Key.IndexOf(query, StringComparison.OrdinalIgnoreCase) < 0
                    && track.Folder.IndexOf(query, StringComparison.OrdinalIgnoreCase) < 0) continue;
                result.Add(i);
            }
            result.Sort(delegate(int left, int right)
            {
                MediaTrack a = mediaDeck.Tracks[left];
                MediaTrack b = mediaDeck.Tracks[right];
                if (mediaSortMode == 1) return b.ModifiedUtcTicks.CompareTo(a.ModifiedUtcTicks);
                if (mediaSortMode == 2)
                {
                    int folder = string.Compare(a.Folder, b.Folder, StringComparison.OrdinalIgnoreCase);
                    return folder != 0 ? folder : string.Compare(a.Title, b.Title, StringComparison.OrdinalIgnoreCase);
                }
                if (mediaSortMode == 3)
                {
                    int aPosition = mediaDeck.QueuePosition(left);
                    int bPosition = mediaDeck.QueuePosition(right);
                    if (aPosition < 0) aPosition = int.MaxValue;
                    if (bPosition < 0) bPosition = int.MaxValue;
                    int queue = aPosition.CompareTo(bPosition);
                    return queue != 0 ? queue : string.Compare(a.Title, b.Title, StringComparison.OrdinalIgnoreCase);
                }
                return string.Compare(a.Title, b.Title, StringComparison.OrdinalIgnoreCase);
            });
            return result;
        }

        private void RefreshMusicLibrary()
        {
            if (musicImportBusy) return;
            musicImportBusy = true;
            status = "Checking the music inbox and preparing OGG tracks…";
            backend.RefreshMusic(delegate(MusicImportResponse response)
            {
                musicImportBusy = false;
                lastMusicInboxRevision = mediaDeck.InboxRevision();
                mediaDeck.Refresh();
                if (response == null)
                {
                    status = "Music refresh returned no response; existing tracks are still available.";
                    mediaDeck.SetStatus(status);
                    return;
                }
                string resultStatus = response.Converted + " audio converted, " + response.VideoCopied + " lyric video" + (response.VideoCopied == 1 ? "" : "s") + " and " + response.LyricsCopied + " lyric sheet" + (response.LyricsCopied == 1 ? "" : "s") + " added, " + response.Skipped + " current; " + response.TrackCount + " total (" + response.VideoCount + " videos)."
                    + (string.IsNullOrEmpty(response.QualityProfile) ? "" : " Quality: " + response.QualityProfile + ".")
                    + (response.ConverterAvailable ? "" : " FFmpeg is not configured, so new MP3/WAV files will use direct playback until it is added.")
                    + (response.Failed == null || response.Failed.Count == 0 ? "" : " Failed: " + response.Failed[0].File + " — " + response.Failed[0].Error);
                status = resultStatus;
                mediaDeck.SetStatus(resultStatus);
                if (evidence != null) evidence.Record("media.refresh", "converted=" + response.Converted + "; copied=" + response.Copied + "; videos=" + response.VideoCount + "; tracks=" + response.TrackCount + "; converter=" + response.ConverterAvailable);
            });
        }

        private float DrawEqSlider(string label, float value)
        {
            GUILayout.BeginHorizontal();
            GUILayout.Label(label, smallStyle, GUILayout.Width(62f));
            float changed = GUILayout.HorizontalSlider(value, -12f, 12f, GUILayout.Width(410f));
            GUILayout.Label(changed.ToString("+0;-0;0") + " dB", smallStyle, GUILayout.Width(64f));
            GUILayout.EndHorizontal();
            return changed;
        }

        private void DrawMediaWaveform(Rect rect, float[] bins)
        {
            GUI.Box(rect, GUIContent.none, panelStyle);
            if (bins == null || bins.Length == 0) return;
            float width = (rect.width - 20f) / bins.Length;
            for (int i = 0; i < bins.Length; i++)
            {
                float height = Mathf.Max(3f, bins[i] * (rect.height - 18f));
                GUI.color = i <= mediaDeck.Progress * bins.Length ? red : new Color(0.55f, 0.32f, 0.29f, 1f);
                GUI.DrawTexture(new Rect(rect.x + 10f + i * width, rect.center.y - height * 0.5f, Mathf.Max(2f, width - 2f), height), whiteTexture);
            }
            GUI.color = Color.white;
        }

        private void DrawWaveform(Rect rect)
        {
            GUI.Box(rect, GUIContent.none, panelStyle);
            float phase = Time.realtimeSinceStartup * (recording ? 6f : 1.2f);
            float liveLevel = recording ? CurrentMicrophoneLevel() : 0f;
            for (int i = 0; i < 35; i++)
            {
                float value = recording ? Mathf.Clamp01(liveLevel * (0.72f + 0.28f * Mathf.Abs(Mathf.Sin(phase + i * 0.7f)))) : 0.15f;
                float height = 12f + value * (rect.height - 24f);
                GUI.color = recording ? red : new Color(0.55f, 0.32f, 0.29f, 1f);
                GUI.DrawTexture(new Rect(rect.x + 10f + i * ((rect.width - 20f) / 35f), rect.center.y - height * 0.5f, 3f, height), whiteTexture);
            }
            GUI.color = Color.white;
        }

        private void DrawRecipeCard(AiRecipe recipe, bool showScores, bool showActions)
        {
            bool isArtwork = recipe.Artwork != null && recipe.Artwork.Enabled && recipe.Placements != null && recipe.Placements.Count > 0;
            GUILayout.BeginVertical(cardStyle);
            GUILayout.BeginHorizontal();
            GUILayout.Label(recipe.Name, titleStyle);
            GUILayout.FlexibleSpace();
            GUILayout.Label(recipe.Shape, tagStyle);
            if (!isArtwork && GUILayout.Button(editRecipe ? "DONE" : "EDIT", editRecipe ? activeButtonStyle : buttonStyle, GUILayout.Width(72f), GUILayout.Height(31f))) editRecipe = !editRecipe;
            GUILayout.EndHorizontal();
            GUILayout.Label(recipe.Summary, bodyStyle);
            if (isArtwork)
            {
                GUILayout.BeginHorizontal();
                GUILayout.Label("ARTWORK", activeButtonStyle, GUILayout.Width(92f), GUILayout.Height(28f));
                GUILayout.Label(recipe.Artwork.Subject, tagStyle);
                GUILayout.Label(recipe.Artwork.Detail + " detail", tagStyle);
                GUILayout.Label(recipe.Placements.Count + " pieces", tagStyle);
                GUILayout.EndHorizontal();
                GUILayout.Label("Precision placement: " + recipe.Artwork.Style + " · " + recipe.Artwork.Symmetry, smallStyle);
            }
            GUILayout.Space(5f);
            for (int i = 0; i < recipe.Ingredients.Count; i++)
            {
                AiRecipeIngredient ingredient = recipe.Ingredients[i];
                GUILayout.BeginHorizontal();
                GUILayout.Label("• " + ingredient.Id, bodyStyle, GUILayout.Width(245f));
                GUILayout.Label(ingredient.Size, smallStyle, GUILayout.Width(85f));
                GUILayout.Label(ingredient.TargetGrams.ToString("0") + " g target", smallStyle);
                GUILayout.EndHorizontal();
                if (editRecipe && !isArtwork)
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
                if (GUILayout.Button("PREVIEW ON PIZZA", buttonStyle, GUILayout.Height(48f))) Preview(recipe, recipes.IndexOf(recipe));
                if (GUILayout.Button("APPLY RECIPE", primaryButtonStyle, GUILayout.Height(48f))) Apply(recipe, recipes.IndexOf(recipe));
                GUILayout.EndHorizontal();
                if (isArtwork)
                {
                    GUILayout.BeginHorizontal();
                    if (GUILayout.Button("REMIX ART", buttonStyle, GUILayout.Height(38f)))
                    {
                        artSeed = artSeed == 0 ? 1301 : artSeed + 7919;
                        Submit("/chat", 1);
                    }
                    if (GUILayout.Button("Detail: " + artDetail, activeButtonStyle, GUILayout.Height(38f))) CycleArtDetail();
                    GUILayout.EndHorizontal();
                    DrawDesignTools(recipe);
                }
                GUILayout.BeginHorizontal();
                if (GUILayout.Button("Save to recipe book", buttonStyle, GUILayout.Height(38f))) SaveToBook();
                if (GUILayout.Button("Start over", buttonStyle, GUILayout.Height(38f))) StartOver();
                GUILayout.EndHorizontal();
            }
            GUILayout.EndVertical();
        }

        private void DrawDesignTools(AiRecipe recipe)
        {
            GUILayout.Space(4f);
            GUILayout.BeginVertical(panelStyle);
            GUILayout.Label("Creative power tools", subtitleStyle);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("AUDITION SWAP", buttonStyle, GUILayout.Height(34f))) AuditionIngredientSwap(recipe);
            if (GUILayout.Button("CONTRAST COACH", buttonStyle, GUILayout.Height(34f))) status = ContrastAdvice(recipe);
            if (GUILayout.Button("COPY PIZZA DNA", buttonStyle, GUILayout.Height(34f)))
            {
                lastPizzaDna = PizzaDna(recipe);
                GUIUtility.systemCopyBuffer = lastPizzaDna;
                status = "Copied reproducible Pizza DNA: " + lastPizzaDna;
            }
            GUILayout.EndHorizontal();
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("CHECKPOINT", activeButtonStyle, GUILayout.Height(34f))) SaveCheckpoint(recipe);
            GUI.enabled = designCheckpoints.Count > 0;
            if (GUILayout.Button("BACK", buttonStyle, GUILayout.Height(34f))) RestoreCheckpoint();
            if (GUILayout.Button("BRANCH", buttonStyle, GUILayout.Height(34f))) BranchCheckpoint(recipe);
            if (GUILayout.Button(checkpointCompare ? "COMPARE ON" : "COMPARE", checkpointCompare ? activeButtonStyle : buttonStyle, GUILayout.Height(34f))) checkpointCompare = !checkpointCompare;
            GUI.enabled = true;
            GUILayout.EndHorizontal();
            GUILayout.Label(lastPizzaDna, smallStyle);
            if (checkpointCompare && designCheckpoints.Count > 0)
            {
                AiRecipe earlier = designCheckpoints[designCheckpoints.Count - 1];
                GUILayout.Label("Checkpoint: " + earlier.Name + " · " + earlier.Placements.Count + " pieces  →  Current: " + recipe.Name + " · " + recipe.Placements.Count + " pieces", smallStyle);
            }
            GUILayout.EndVertical();
        }

        private void SaveCheckpoint(AiRecipe recipe)
        {
            designCheckpoints.Add(CloneRecipe(recipe));
            if (designCheckpoints.Count > 8) designCheckpoints.RemoveAt(0);
            status = "Checkpoint " + designCheckpoints.Count + " saved. You can audition, branch, or go back safely.";
            if (evidence != null) evidence.Record("design.checkpoint", "dna=" + PizzaDna(recipe) + "; count=" + designCheckpoints.Count);
        }

        private void RestoreCheckpoint()
        {
            if (designCheckpoints.Count == 0) return;
            AiRecipe restored = designCheckpoints[designCheckpoints.Count - 1];
            designCheckpoints.RemoveAt(designCheckpoints.Count - 1);
            if (recipes.Count == 0) recipes.Add(restored); else recipes[Mathf.Clamp(selectedRecipe, 0, recipes.Count - 1)] = restored;
            lastPizzaDna = PizzaDna(restored);
            status = "Restored the previous design checkpoint.";
            Preview(restored, selectedRecipe);
        }

        private void BranchCheckpoint(AiRecipe recipe)
        {
            AiRecipe branch = CloneRecipe(recipe);
            string branchName = branch.Name + " — Branch " + (recipes.Count + 1);
            branch.Name = branchName.Substring(0, Mathf.Min(60, branchName.Length));
            recipes.Add(branch);
            selectedRecipe = recipes.Count - 1;
            lastPizzaDna = PizzaDna(branch);
            status = "Created an editable branch without losing the original.";
        }

        private void AuditionIngredientSwap(AiRecipe recipe)
        {
            if (recipe.Artwork == null || recipe.Artwork.Palette == null || recipe.Artwork.Palette.Count < 2)
            {
                status = "This design needs at least two palette roles for an audition.";
                return;
            }
            SaveCheckpoint(recipe);
            List<string> keys = new List<string>(recipe.Artwork.Palette.Keys);
            keys.Sort(StringComparer.OrdinalIgnoreCase);
            string first = keys[0];
            string second = keys[1];
            string firstId = recipe.Artwork.Palette[first];
            string secondId = recipe.Artwork.Palette[second];
            recipe.Artwork.Palette[first] = secondId;
            recipe.Artwork.Palette[second] = firstId;
            for (int i = 0; i < recipe.Placements.Count; i++)
            {
                if (recipe.Placements[i].Role == first) recipe.Placements[i].IngredientId = secondId;
                else if (recipe.Placements[i].Role == second) recipe.Placements[i].IngredientId = firstId;
            }
            for (int i = 0; i < recipe.Ingredients.Count; i++)
            {
                if (recipe.Ingredients[i].Id == firstId) recipe.Ingredients[i].Id = secondId;
                else if (recipe.Ingredients[i].Id == secondId) recipe.Ingredients[i].Id = firstId;
            }
            recipe.Name = recipe.Name.Replace(" — Audition", "") + " — Audition";
            lastPizzaDna = PizzaDna(recipe);
            status = "Auditioning " + firstId + " ↔ " + secondId + ". Use BACK to compare the original.";
            Preview(recipe, selectedRecipe);
        }

        private static string ContrastAdvice(AiRecipe recipe)
        {
            bool dark = false;
            bool light = false;
            bool warm = false;
            bool cool = false;
            for (int i = 0; i < recipe.Placements.Count; i++)
            {
                string role = recipe.Placements[i].Role;
                dark |= role == "dark" || role == "brown" || role == "purple";
                light |= role == "white" || role == "skin" || role == "yellow";
                warm |= role == "red" || role == "orange" || role == "pink";
                cool |= role == "green" || role == "purple";
            }
            if (!dark || !light) return "Contrast Coach: add both a dark outline ingredient and a light highlight so the picture reads after baking.";
            if (!warm || !cool) return "Contrast Coach: value contrast is strong; add one warm/cool counter-color to separate the focal feature.";
            return "Contrast Coach: strong dark/light and warm/cool separation. Keep small highlights away from similarly colored regions.";
        }

        private static string PizzaDna(AiRecipe recipe)
        {
            unchecked
            {
                uint hash = 2166136261;
                string text = recipe.Name + "|" + recipe.Seed + "|" + recipe.Shape + "|" + recipe.Placements.Count;
                for (int i = 0; i < recipe.Placements.Count; i++)
                    text += "|" + recipe.Placements[i].IngredientId + ":" + recipe.Placements[i].X.ToString("0.000") + ":" + recipe.Placements[i].Y.ToString("0.000");
                for (int i = 0; i < text.Length; i++) { hash ^= text[i]; hash *= 16777619; }
                return "BARROS-" + hash.ToString("X8") + "-" + recipe.Placements.Count.ToString("000");
            }
        }

        private static AiRecipe CloneRecipe(AiRecipe recipe)
        {
            return JsonConvert.DeserializeObject<AiRecipe>(JsonConvert.SerializeObject(recipe));
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
            string sendLabel = guidedActive && mode == DesignerMode.Chat && chatAction == "Build with me" ? "ADD STEP  ➜" : "SEND  ➜";
            if (GUI.Button(new Rect(rect.x + rect.width - 111f, rect.y + 33f, 101f, 77f), busy ? "WORKING…" : sendLabel, primaryButtonStyle))
            {
                if (guidedActive && mode == DesignerMode.Chat && chatAction == "Build with me") AdvanceGuidedSession();
                else if (mode == DesignerMode.Lab) Submit("/lab", 3);
                else if (mode == DesignerMode.Crew) Submit("/crew", 1);
                else Submit("/chat", 1);
            }
            GUI.enabled = true;
            if (GUI.Button(new Rect(rect.x + 10f, rect.y + 119f, 78f, 39f), "Attach", buttonStyle)) Attach();
            if (GUI.Button(new Rect(rect.x + 94f, rect.y + 119f, 76f, 39f), recording ? "Stop mic" : (HasMicrophone() ? "Mic" : "No mic"), buttonStyle))
            {
                if (recording) StopVoiceAndTranscribe(); else StartVoice();
            }
            if (GUI.Button(new Rect(rect.x + 176f, rect.y + 119f, 93f, 39f), "History", showHistory ? activeButtonStyle : buttonStyle)) showHistory = !showHistory;
            if (GUI.Button(new Rect(rect.x + 275f, rect.y + 119f, 91f, 39f), shape, buttonStyle)) CycleShape();
            if (GUI.Button(new Rect(rect.x + 372f, rect.y + 119f, 88f, 39f), heat, buttonStyle)) CycleHeat();
            string ideasLabel = "Ideas " + (useInspirationLibrary ? "ON" : "OFF");
            if (attachments.Count > 0) ideasLabel += " · " + attachments.Count + " file" + (attachments.Count == 1 ? "" : "s");
            if (GUI.Button(new Rect(rect.x + 467f, rect.y + 119f, 132f, 39f), ideasLabel, useInspirationLibrary ? activeButtonStyle : buttonStyle))
            {
                useInspirationLibrary = !useInspirationLibrary;
                status = useInspirationLibrary
                    ? "Local inspiration is on. Up to three indexed designs may guide the next request."
                    : "Local inspiration is off. Only manually attached files will be used.";
            }
        }

        private void StartGuidedSession()
        {
            guidedActive = true;
            guidedStep = 0;
            guidedAnswers.Clear();
            prompt = "";
            status = "Guided session started. Answer step 1 in the message box.";
            conversation.Add(new ConversationLine("Creative Director", GuidedQuestions[0]));
            if (evidence != null) evidence.Record("guided.started", "steps=" + guidedStepCount + "; tone=" + guidedTone);
        }

        private void AdvanceGuidedSession()
        {
            string answer = (prompt ?? "").Trim();
            if (string.IsNullOrEmpty(answer))
            {
                status = "Add a short answer for this step first.";
                return;
            }
            guidedAnswers.Add(answer);
            conversation.Add(new ConversationLine("You", answer));
            string[] crew = { "Creative Director", "Flavor Chef", "Customer Scout", "Cost Manager" };
            string agent = crew[guidedStep % crew.Length];
            string reaction = "Captured. That gives the design a concrete decision.";
            if (guidedTone == "Playful") reaction = guidedStep % 2 == 0 ? "Nice choice — this pizza is starting to have a personality. 🍕" : "Locked in. The topping crew approves this delicious plot twist.";
            if (guidedTone == "Goofball") reaction = guidedStep % 2 == 0 ? "Official topping science says: excellent. The olives are taking notes. 😄" : "Knock knock. Who's there? A much better pizza plan. 🍕";
            conversation.Add(new ConversationLine(agent, reaction));
            if (!agentVoicesMuted && ttsConfigured) SpeakAgent(agent, reaction);
            guidedStep++;
            prompt = "";
            if (guidedStep < guidedStepCount)
            {
                string nextAgent = crew[guidedStep % crew.Length];
                conversation.Add(new ConversationLine(nextAgent, GuidedQuestions[guidedStep]));
                status = "Step " + (guidedStep + 1) + " of " + guidedStepCount + ".";
                return;
            }
            string brief = "Create a complete pizza from this " + guidedTone.ToLowerInvariant() + " guided design brief: ";
            for (int i = 0; i < guidedAnswers.Count; i++) brief += (i + 1) + ") " + guidedAnswers[i] + (i + 1 == guidedAnswers.Count ? "." : "; ");
            guidedActive = false;
            guidedBuildPending = true;
            prompt = brief;
            status = "The guided brief is complete. The crew is building the pizza now…";
            if (evidence != null) evidence.Record("guided.completed", "steps=" + guidedAnswers.Count + "; characters=" + brief.Length);
            Submit("/chat", 1);
        }

        private void CancelGuidedSession()
        {
            guidedActive = false;
            guidedStep = 0;
            guidedAnswers.Clear();
            prompt = "";
            status = "Guided session cancelled. Start again whenever you are ready.";
        }

        private void Submit(string endpoint, int count)
        {
            if (busy) return;
            if (!backendReady)
            {
                backend.Health(delegate(bool ready, string label, bool inputReady, bool speechReady)
                {
                    backendReady = ready;
                    backendLabel = ready ? label : "Backend unavailable";
                    sttConfigured = inputReady;
                    ttsConfigured = speechReady;
                    if (ready) Submit(endpoint, count);
                    else status = "Local AI backend is not running. Use the diagnostic script.";
                });
                return;
            }
            string effective = prompt.Trim();
            if (chatAction == "Pizza art" && endpoint == "/chat")
            {
                if (string.IsNullOrEmpty(effective)) effective = "Create a detailed Santa Claus pizza picture.";
                effective = "Create a " + artDetail.ToLowerInvariant() + "-detail " + artStyle.ToLowerInvariant() + " ingredient pizza artwork using a " + artPalette.ToLowerInvariant() + " palette and " + artSymmetry.ToLowerInvariant() + " symmetry, with deliberate color, shape, outline and facial-feature placement. " + effective;
            }
            if (chatAction == "Surprise me" && endpoint == "/chat") effective = "Surprise me with a distinctive, game-valid pizza. " + effective;
            if (chatAction == "Improve this" && endpoint == "/chat") effective = "Improve the current pizza while preserving its idea. " + effective;
            if (string.IsNullOrEmpty(effective)) effective = "Surprise me with a distinctive crowd favorite.";
            AiRequest request = new AiRequest();
            request.Prompt = effective;
            request.Count = count;
            request.Seed = chatAction == "Pizza art" ? artSeed : 0;
            request.Catalog = game.BuildCatalog();
            request.CurrentPizza = game.DescribeCurrentPizza();
            request.Constraints.Heat = heat;
            request.Constraints.Shape = shape;
            request.Constraints.PriceCeiling = priceCeiling;
            request.Constraints.ProfitFactor = profitFactor;
            request.Attachments.AddRange(attachments);
            request.UseInspirationLibrary = useInspirationLibrary;
            request.FocusAgent = endpoint == "/crew" ? crewFocusAgent : "";
            bool submittedByVoice = promptFromVoice;
            promptFromVoice = false;
            conversation.Add(new ConversationLine(submittedByVoice ? "You (voice)" : "You", effective));
            busy = true;
            status = endpoint == "/crew"
                ? (string.IsNullOrEmpty(request.FocusAgent)
                    ? "The four agents are debating…"
                    : "Asking " + request.FocusAgent + " for a focused review…")
                : (chatAction == "Pizza art"
                    ? "Painting a precise ingredient artwork plan…"
                    : (useInspirationLibrary ? "Designing with the local inspiration library…" : "Designing and validating against the live catalog…"));
            backend.Compose(endpoint, request, delegate(AiResponse response)
            {
                busy = false;
                if (response == null || !response.Ok)
                {
                    guidedBuildPending = false;
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
                if (endpoint == "/crew")
                    for (int i = 0; i < agents.Count; i++)
                        conversation.Add(new ConversationLine(agents[i].Agent, agents[i].Message));
                consensus = response.Consensus;
                selectedRecipe = 0;
                attachments.Clear();
                status = response.Message;
                conversation.Add(new ConversationLine("Barro's AI", response.Message));
                if (recipes.Count > 0) conversation.Add(new ConversationLine("Barro's AI", "Drafted “" + recipes[0].Name + "”. Preview it on the real dough or apply it."));
                if (guidedBuildPending && recipes.Count > 0)
                {
                    conversation.Add(new ConversationLine("Creative Director", "Your guided pizza is ready. Preview it, apply it if you approve, then tell me: do you want to save it to the recipe book now?"));
                    status = "Guided pizza ready · Preview, Apply, then Save to recipe book when you approve.";
                }
                guidedBuildPending = false;
                if (submittedByVoice)
                {
                    if (!ttsConfigured)
                        status += " Text reply is ready; Azure agent speech still needs setup.";
                    else if (agentVoicesMuted)
                        status += " Text reply is ready; turn Agent voices ON to hear it.";
                    else
                    {
                        voiceResumeAfterSpeech = voiceAutoContinue;
                        if (endpoint == "/crew" && agents.Count > 0) QueueAgentRoundtable();
                        else SpeakAgent("Creative Director", response.Message);
                    }
                }
                else if (endpoint == "/crew" && !agentVoicesMuted && ttsConfigured && agents.Count > 0)
                    QueueAgentRoundtable();
            });
        }

        private void SelectArtTemplate(string template)
        {
            artTemplate = template;
            string subject = template == "Tree" ? "Christmas tree" : template;
            prompt = "Create a detailed " + subject + " pizza picture with a clear silhouette, readable features and balanced ingredient colors.";
            status = template + " selected. Add any colors or expression you want, then press Send.";
        }

        private void FocusAgent(string agent)
        {
            if (busy) return;
            crewFocusAgent = agent;
            if (string.IsNullOrEmpty(prompt.Trim())) prompt = "Review the current pizza and suggest the single most useful improvement.";
            status = "Asking " + agent + " for a focused review…";
            Submit("/crew", 1);
        }

        private string AgentVoiceLabel(string agent)
        {
            int index;
            if (!agentVoiceIndexes.TryGetValue(agent, out index)) index = 0;
            return VoiceLabels[Mathf.Clamp(index, 0, VoiceLabels.Length - 1)];
        }

        private string AgentVoiceName(string agent)
        {
            int index;
            if (!agentVoiceIndexes.TryGetValue(agent, out index)) index = 0;
            return VoiceNames[Mathf.Clamp(index, 0, VoiceNames.Length - 1)];
        }

        private void CycleAgentVoice(string agent)
        {
            int index;
            if (!agentVoiceIndexes.TryGetValue(agent, out index)) index = 0;
            agentVoiceIndexes[agent] = (index + 1) % VoiceNames.Length;
            status = agent + " now uses " + AgentVoiceLabel(agent) + ".";
        }

        private void SpeakAgent(string agent, string message)
        {
            if (!ttsConfigured)
            {
                status = "Azure agent voices need setup before they can speak.";
                return;
            }
            if (agentVoicesMuted)
            {
                status = "Agent voices are muted. Turn them on at the top of Design Crew.";
                return;
            }
            agentSpeechQueue.Add(new AgentSpeechTurn(agent, message, AgentVoiceName(agent)));
            status = agentSpeechBusy ? agent + " added to the voice queue." : "Preparing " + agent + " voice…";
            if (!agentSpeechBusy) BeginNextAgentSpeech();
        }

        private void QueueAgentRoundtable()
        {
            if (!ttsConfigured) { status = "Azure agent voices need setup before the roundtable can speak."; return; }
            if (agentVoicesMuted) { status = "Agent voices are muted. Turn them on to play the roundtable."; return; }
            if (agents.Count == 0) { status = "Ask the Design Crew first, then play their roundtable."; return; }
            for (int i = 0; i < agents.Count; i++)
                agentSpeechQueue.Add(new AgentSpeechTurn(agents[i].Agent, agents[i].Message, AgentVoiceName(agents[i].Agent)));
            status = "Queued all " + agents.Count + " agents. They will speak one at a time without overlap.";
            if (!agentSpeechBusy) BeginNextAgentSpeech();
        }

        private void QueueVoiceCheck()
        {
            if (!ttsConfigured)
            {
                status = "Azure agent voices need setup before the voice check can run.";
                return;
            }
            StopAgentSpeech();
            agentVoicesMuted = false;
            agentSpeechQueue.Add(new AgentSpeechTurn("Flavor Chef", "Flavor Chef ready. I will keep every pizza bold and delicious.", AgentVoiceName("Flavor Chef")));
            agentSpeechQueue.Add(new AgentSpeechTurn("Cost Manager", "Cost Manager ready. I will protect the budget without flattening the idea.", AgentVoiceName("Cost Manager")));
            agentSpeechQueue.Add(new AgentSpeechTurn("Customer Scout", "Customer Scout ready. I will keep the design inviting and memorable.", AgentVoiceName("Customer Scout")));
            agentSpeechQueue.Add(new AgentSpeechTurn("Creative Director", "Creative Director ready. We will speak one at a time and build together.", AgentVoiceName("Creative Director")));
            status = "Voice check queued. Music will remain paused until all four agents finish.";
            BeginNextAgentSpeech();
        }

        private void BeginNextAgentSpeech()
        {
            if (agentSpeechQueue.Count == 0)
            {
                bool resumeVoice = voiceResumeAfterSpeech;
                voiceResumeAfterSpeech = false;
                agentSpeechBusy = false;
                currentSpeakingAgent = "";
                if (agentSpeechFocusHeld && mediaDeck != null) mediaDeck.EndSpeechFocus();
                agentSpeechFocusHeld = false;
                agentSpeechHasPlayed = false;
                status = resumeVoice
                    ? "Agent roundtable finished. Chef Voice will listen for your next turn."
                    : "Agent roundtable finished. Background music resumed if it was playing.";
                if (resumeVoice && sttConfigured && HasMicrophone() && !microphoneMuted)
                {
                    if (voiceResumeRoutine != null) StopCoroutine(voiceResumeRoutine);
                    voiceResumeRoutine = StartCoroutine(ResumeVoiceAfterAgents());
                }
                return;
            }
            agentSpeechBusy = true;
            if (!agentSpeechFocusHeld)
            {
                if (mediaDeck != null) mediaDeck.BeginSpeechFocus();
                agentSpeechFocusHeld = true;
            }
            AgentSpeechTurn turn = agentSpeechQueue[0];
            agentSpeechQueue.RemoveAt(0);
            currentSpeakingAgent = turn.Agent;
            status = "Preparing " + turn.Agent + " · " + agentSpeechQueue.Count + " waiting…";
            int generation = agentSpeechGeneration;
            backend.Speak(turn.Agent, turn.Message, turn.Voice, agentSpeechRate, delegate(SpeechResponse response)
            {
                if (generation != agentSpeechGeneration || !agentSpeechBusy) return;
                if (response == null || !response.Ok || string.IsNullOrEmpty(response.AudioBase64))
                {
                    status = response == null ? "No speech response." : response.Error;
                    BeginNextAgentSpeech();
                    return;
                }
                try
                {
                    byte[] wav = Convert.FromBase64String(response.AudioBase64);
                    agentSpeechClip = WavDecoder.Decode(wav, "Barros-" + turn.Agent.Replace(" ", "-"));
                    agentAudioSource.clip = agentSpeechClip;
                    agentAudioSource.volume = agentVoiceVolume;
                    agentSpeechRoutine = StartCoroutine(PlayAgentSpeechTurn(turn.Agent, response.Label, response.Voice, wav.Length));
                }
                catch (Exception exception) { status = "Agent voice playback failed: " + exception.Message; BeginNextAgentSpeech(); }
            });
        }

        private IEnumerator PlayAgentSpeechTurn(string agent, string label, string voice, int wavBytes)
        {
            float pause = agentSpeechHasPlayed ? agentSpeechGap : 1f;
            status = "Music paused · " + agent + " speaks in " + pause.ToString("0.00") + " seconds…";
            yield return new WaitForSecondsRealtime(pause);
            if (agentAudioSource == null || agentSpeechClip == null)
            {
                agentSpeechRoutine = null;
                BeginNextAgentSpeech();
                yield break;
            }
            agentAudioSource.Play();
            status = agent + " speaking with " + label + " · " + agentSpeechQueue.Count + " waiting.";
            if (evidence != null) evidence.Record("voice.agent.played", "agent=" + agent + "; voice=" + voice + "; wav_bytes=" + wavBytes + "; rate=" + agentSpeechRate + "; queued=" + agentSpeechQueue.Count);
            while (agentAudioSource != null && agentAudioSource.isPlaying) yield return null;
            if (agentSpeechClip != null) Destroy(agentSpeechClip);
            agentSpeechClip = null;
            agentSpeechHasPlayed = true;
            agentSpeechRoutine = null;
            BeginNextAgentSpeech();
        }

        private void StopAgentSpeech()
        {
            agentSpeechGeneration++;
            agentSpeechQueue.Clear();
            if (agentSpeechRoutine != null) StopCoroutine(agentSpeechRoutine);
            agentSpeechRoutine = null;
            if (agentAudioSource != null) agentAudioSource.Stop();
            if (agentSpeechClip != null) Destroy(agentSpeechClip);
            agentSpeechClip = null;
            agentSpeechBusy = false;
            currentSpeakingAgent = "";
            if (agentSpeechFocusHeld && mediaDeck != null) mediaDeck.EndSpeechFocus();
            agentSpeechFocusHeld = false;
            agentSpeechHasPlayed = false;
            voiceResumeAfterSpeech = false;
            if (voiceResumeRoutine != null) StopCoroutine(voiceResumeRoutine);
            voiceResumeRoutine = null;
            status = "Agent voice queue stopped.";
        }

        private IEnumerator ResumeVoiceAfterAgents()
        {
            yield return new WaitForSecondsRealtime(0.9f);
            voiceResumeRoutine = null;
            if (mode == DesignerMode.Voice && !recording && !busy && voiceAutoContinue && sttConfigured && HasMicrophone() && !microphoneMuted)
                StartVoice();
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

        private void CycleArtDetail()
        {
            if (string.Equals(artDetail, "Draft", StringComparison.OrdinalIgnoreCase)) artDetail = "Standard";
            else if (string.Equals(artDetail, "Standard", StringComparison.OrdinalIgnoreCase)) artDetail = "High";
            else artDetail = "Draft";
            status = "Pizza Art detail set to " + artDetail + ". Generate or remix to rebuild the placement plan.";
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
                status = "Saved the current pizza to the recipe book.";
                StartCoroutine(ReactivateAiTab());
            }
            catch (Exception exception) { status = "Save failed: " + exception.Message; }
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
            RefreshMicrophones();
            if (microphoneMuted)
            {
                pendingVoiceError = "The microphone is muted. Press Muted to enable it.";
                status = pendingVoiceError;
                return;
            }
            if (!HasMicrophone())
            {
                pendingVoiceError = "No Windows recording device is active. Connect or enable a microphone, then press Retry microphone.";
                status = pendingVoiceError;
                if (evidence != null) evidence.Record("voice.capture.failed", pendingVoiceError);
                return;
            }
            try
            {
                string device = SelectedMicrophoneDevice();
                voiceClip = Microphone.Start(device, false, 30, 16000);
                recording = voiceClip != null;
                recordingStarted = Time.realtimeSinceStartup;
                status = recording ? "Listening… click Stop when finished." : "Could not start the microphone.";
                if (evidence != null) evidence.Record(recording ? "voice.capture.started" : "voice.capture.failed", "device=" + device + "; devices=" + Microphone.devices.Length + "; rate=16000; gain=" + microphoneGain);
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

        private static bool HasMicrophone()
        {
            try { return Microphone.devices != null && Microphone.devices.Length > 0; }
            catch { return false; }
        }

        private void RefreshMicrophones()
        {
            try
            {
                string[] devices = Microphone.devices;
                if (devices == null || devices.Length == 0)
                {
                    selectedMicrophone = 0;
                    selectedMicrophoneName = "";
                    return;
                }
                int existing = -1;
                for (int i = 0; i < devices.Length; i++)
                    if (string.Equals(devices[i], selectedMicrophoneName, StringComparison.OrdinalIgnoreCase)) { existing = i; break; }
                selectedMicrophone = existing >= 0 ? existing : Mathf.Clamp(selectedMicrophone, 0, devices.Length - 1);
                selectedMicrophoneName = devices[selectedMicrophone];
                if (!recording) status = devices.Length + " microphone input" + (devices.Length == 1 ? "" : "s") + " found · " + selectedMicrophoneName + " selected.";
            }
            catch (Exception exception) { pendingVoiceError = "Microphone refresh failed: " + exception.Message; }
        }

        private void CycleMicrophone()
        {
            RefreshMicrophones();
            string[] devices = Microphone.devices;
            if (devices == null || devices.Length == 0) { status = "No Windows recording device is active."; return; }
            selectedMicrophone = (selectedMicrophone + 1) % devices.Length;
            selectedMicrophoneName = devices[selectedMicrophone];
            status = "Microphone selected: " + selectedMicrophoneName + ".";
        }

        private string SelectedMicrophoneDevice()
        {
            string[] devices = Microphone.devices;
            if (devices == null || devices.Length == 0) return null;
            selectedMicrophone = Mathf.Clamp(selectedMicrophone, 0, devices.Length - 1);
            selectedMicrophoneName = devices[selectedMicrophone];
            return selectedMicrophoneName;
        }

        private string SelectedMicrophoneLabel()
        {
            string value = SelectedMicrophoneDevice();
            if (string.IsNullOrEmpty(value)) return "Windows default input";
            return value.Length > 34 ? value.Substring(0, 31) + "…" : value;
        }

        private float CurrentMicrophoneLevel()
        {
            if (!recording || voiceClip == null) return 0f;
            try
            {
                string device = SelectedMicrophoneDevice();
                int position = Microphone.GetPosition(device);
                if (position < 2) return 0f;
                int frames = Mathf.Min(128, position);
                float[] samples = new float[frames * Mathf.Max(1, voiceClip.channels)];
                if (!voiceClip.GetData(samples, Mathf.Max(0, position - frames))) return 0f;
                float peak = 0f;
                for (int i = 0; i < samples.Length; i++) peak = Mathf.Max(peak, Mathf.Abs(samples[i] * microphoneGain));
                return Mathf.Clamp01(peak * 3f);
            }
            catch { return 0f; }
        }

        private void CancelVoiceRecording()
        {
            if (!recording) return;
            try { Microphone.End(SelectedMicrophoneDevice()); }
            catch { }
            recording = false;
            if (voiceClip != null) Destroy(voiceClip);
            voiceClip = null;
            status = "Microphone recording cancelled.";
        }

        private void StopVoiceAndTranscribe()
        {
            if (!recording || voiceClip == null) return;
            recording = false;
            string device = SelectedMicrophoneDevice();
            int position = Mathf.Max(1, Microphone.GetPosition(device));
            Microphone.End(device);
            AudioClip trimmed = AudioClip.Create("BarrosVoice", position, voiceClip.channels, voiceClip.frequency, false);
            float[] samples = new float[position * voiceClip.channels];
            voiceClip.GetData(samples, 0);
            for (int i = 0; i < samples.Length; i++) samples[i] = Mathf.Clamp(samples[i] * microphoneGain, -1f, 1f);
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
                promptFromVoice = true;
                status = voiceUseCrew ? "Voice transcribed. Asking the full Design Crew…" : "Voice transcribed. Asking the Pizza Designer…";
                if (evidence != null) evidence.Record("voice.transcription.success", "characters=" + transcript.Length);
                Submit(voiceUseCrew ? "/crew" : "/chat", 1);
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
            Color parchmentEdge = new Color(0.50f, 0.29f, 0.25f, 0.62f);
            Color cardEdge = new Color(0.57f, 0.37f, 0.32f, 0.50f);
            parchmentTexture = LoadExportedSkin("panel.png") ?? Rounded(parchment, parchmentEdge, 12, 1);
            cardTexture = LoadExportedSkin("card.png") ?? Rounded(card, cardEdge, 11, 1);
            maroonTexture = LoadExportedSkin("active.png") ?? Rounded(maroon, new Color(0.30f, 0.09f, 0.08f, 1f), 10, 1);
            redTexture = LoadExportedSkin("primary.png") ?? Rounded(red, new Color(0.43f, 0.08f, 0.08f, 1f), 10, 1);
            lightTexture = LoadExportedSkin("button.png") ?? Rounded(parchmentLight, cardEdge, 10, 1);
            connectionPulseTexture = LoadExportedSkin("connection-pulse.png");
            greenTexture = Solid(green);
            amberTexture = Solid(amber);
            whiteTexture = Solid(Color.white);
            Font font = gameFont != null ? gameFont : Resources.GetBuiltinResource<Font>("Arial.ttf");
            panelStyle = BoxStyle(parchmentTexture, 12, font);
            cardStyle = BoxStyle(cardTexture, 11, font);
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
            inputStyle.border = new RectOffset(10, 10, 10, 10);
            inputStyle.normal.background = lightTexture;
            inputStyle.normal.textColor = ink;
            tagStyle = new GUIStyle(buttonStyle);
            tagStyle.fontSize = 12;
            tagStyle.alignment = TextAnchor.MiddleCenter;
            mediaTrackButtonStyle = MediaTrackStyle(buttonStyle);
            mediaTrackActiveButtonStyle = MediaTrackStyle(activeButtonStyle);
        }

        private Texture2D LoadExportedSkin(string fileName)
        {
            try
            {
                string gameRoot = Directory.GetParent(Application.dataPath).FullName;
                string path = Path.Combine(gameRoot, "BarrosAI", "assets", "ui", "generated", fileName);
                FileInfo info = new FileInfo(path);
                if (!info.Exists || info.Length <= 0 || info.Length > 5 * 1024 * 1024) return null;
                Texture2D texture = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                if (!texture.LoadImage(File.ReadAllBytes(path)) || texture.width < 16 || texture.height < 16 ||
                    texture.width > 512 || texture.height > 512)
                {
                    Destroy(texture);
                    return null;
                }
                texture.wrapMode = TextureWrapMode.Clamp;
                texture.filterMode = FilterMode.Bilinear;
                texture.hideFlags = HideFlags.HideAndDontSave;
                if (!exportedThemeEvidenceRecorded && evidence != null)
                {
                    exportedThemeEvidenceRecorded = true;
                    evidence.Record("ui.exported_theme_loaded", "format=png; source=BarrosCreatorUiLab2021; target=Unity2017");
                }
                return texture;
            }
            catch (Exception)
            {
                return null;
            }
        }

        private static GUIStyle MediaTrackStyle(GUIStyle source)
        {
            GUIStyle style = new GUIStyle(source);
            style.fontSize = 13;
            style.wordWrap = true;
            style.clipping = TextClipping.Clip;
            style.padding = new RectOffset(7, 7, 5, 5);
            return style;
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
            style.margin = new RectOffset(3, 3, 4, 4);
            style.border = new RectOffset(11, 11, 11, 11);
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
            style.margin = new RectOffset(3, 3, 3, 3);
            style.border = new RectOffset(10, 10, 10, 10);
            return style;
        }

        private Texture2D Rounded(Color fill, Color outline, int radius, int outlineWidth)
        {
            const int size = 32;
            Texture2D texture = new Texture2D(size, size, TextureFormat.RGBA32, false);
            texture.wrapMode = TextureWrapMode.Clamp;
            texture.filterMode = FilterMode.Bilinear;
            Color clear = new Color(0f, 0f, 0f, 0f);
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float px = x + 0.5f;
                    float py = y + 0.5f;
                    float nearestX = Mathf.Clamp(px, radius, size - radius);
                    float nearestY = Mathf.Clamp(py, radius, size - radius);
                    float dx = px - nearestX;
                    float dy = py - nearestY;
                    float distance = Mathf.Sqrt(dx * dx + dy * dy);
                    float alpha = Mathf.Clamp01(radius + 0.5f - distance);
                    if (alpha <= 0f)
                    {
                        texture.SetPixel(x, y, clear);
                        continue;
                    }
                    int innerRadius = Mathf.Max(1, radius - outlineWidth);
                    float innerX = Mathf.Clamp(px, radius, size - radius);
                    float innerY = Mathf.Clamp(py, radius, size - radius);
                    float innerDx = px - innerX;
                    float innerDy = py - innerY;
                    bool borderPixel = Mathf.Sqrt(innerDx * innerDx + innerDy * innerDy) > innerRadius ||
                        px < outlineWidth || py < outlineWidth || px > size - outlineWidth || py > size - outlineWidth;
                    Color pixel = borderPixel ? outline : fill;
                    pixel.a *= alpha;
                    texture.SetPixel(x, y, pixel);
                }
            }
            texture.Apply();
            texture.hideFlags = HideFlags.HideAndDontSave;
            return texture;
        }

        private Texture2D Solid(Color color)
        {
            Texture2D texture = new Texture2D(2, 2, TextureFormat.RGBA32, false);
            texture.SetPixels(new Color[] { color, color, color, color });
            texture.Apply();
            texture.hideFlags = HideFlags.HideAndDontSave;
            return texture;
        }

        private sealed class AgentSpeechTurn
        {
            public readonly string Agent;
            public readonly string Message;
            public readonly string Voice;

            public AgentSpeechTurn(string agent, string message, string voice)
            {
                Agent = agent ?? "Agent";
                Message = message ?? "";
                Voice = voice ?? "";
            }
        }
    }
}
