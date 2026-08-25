# Barro's AI Pizza Designer for Pizza Creator

Version **1.0.0-rc1** — an in-game AI design layer for the standalone Windows x64 build of **Pizza Connection 3 - Pizza Creator**.

It adds one real fifth tab to the existing Bakehouse panel and keeps every workflow inside that space:

- **Chat** — Build with me, Surprise me, Improve this, conversation history, attachments and live recipe cards.
- **AI Lab** — three game-valid alternatives with native Preview and Use actions.
- **Design Crew** — Flavor Chef, Cost Manager, Customer Scout and Creative Director with individual opinions and consensus scoring.
- **Chef Voice** — Windows microphone capture and OpenAI-compatible/Whisper transcription.

The design follows the four supplied UI mockups while using the game's warm parchment, maroon and wood visual language. It does not replace `Assembly-CSharp.dll`, patch saves, or fake mouse input.

The AI tab also replaces the plain **Bakehouse** text only while active with the bundled compact **BARRO'S PIZZA CREATOR** header artwork. It aspect-fits inside the title strip and leaves the stock close button unobstructed; the original Bakehouse label returns on every other tab.

## Install

1. Close Pizza Creator.
2. Extract this ZIP somewhere outside the game folder.
3. Double-click **`INSTALL_Barros_AI_Designer.bat`**.
4. The installer defaults to `S:\Unity_Games\PC3 - Pizza Creator`. Browse if the game has moved.
5. Launch **Pizza Connection 3 - Pizza Creator** normally and enter the Bakehouse.
6. Select the new chef-chat tab. Press **F10** to reopen it at any time in the Creator.

The first installation downloads and SHA-256 verifies the official BepInEx 5.4.23.5 x64 loader and a private Python 3.12.10 embedded runtime. It makes no system Python or PATH changes. If either dependency is already installed and compatible, it is reused.

Offline recipe design works immediately. Voice transcription and model-generated reasoning need a configured provider; double-click **`CONFIGURE_AI_PROVIDER.bat`** after installation.

## Using the panel

### Chat

Choose Build with me, Surprise me or Improve this. Describe the pizza and optionally attach a PNG/JPG/WEBP, JSON recipe, TXT or Markdown note. A vision-capable provider receives attached images. The result is repaired against the live 87-item game catalog before it reaches Unity.

### AI Lab

Set heat and shape from the bottom controls, describe the goal, and choose **Generate 3**. Each candidate displays Taste, Cost, Profit, Popularity, Novelty and Originality. **Preview** places it on the real dough without committing; **Start over** restores the pre-preview pizza.

### Design Crew

The four personas review one validated draft. Each has a separate opinion and score, followed by a consensus card. Offline mode uses deterministic specialist rules; an online/local model gives each persona an independent model call.

### Chef Voice

Choose Start Listening, speak for up to 30 seconds, then Stop & Transcribe. The transcript becomes a normal recipe request. Speech-to-text requires a configured STT endpoint; keyboard, attachments and all offline design features remain available without it.

### Applying and saving

**Preview on pizza** and **Apply recipe** invoke the real `IPizzaCreatorService.LoadPizzaFromModel` flow. Ingredients are instantiated by the game's own renderer. **Save to recipe book** invokes the existing Creator recipe-book method. The ordinary game Save button remains available.

## Scores

| Score | Source |
|---|---|
| Taste | Average of the real `CitizenTypeController.RatePizzaRecipe` results |
| Popularity | Average of the real `RatePizzaOverallTaste` results |
| Cost | `PizzaModel.CalculateCosts()` from actual placed ingredient sizes |
| Profit | Actual `PizzaModel` cost, price and profit factor |
| Novelty | Deterministic catalog craziness + ingredient-count heuristic |
| Originality | Deterministic layout-distribution + catalog craziness heuristic |

The backend estimate is replaced with these game-native values once a candidate is bound in Unity.

## Providers

| Provider | Typical endpoint | Notes |
|---|---|---|
| Offline | none | Built in; deterministic and always available |
| LM Studio / OpenAI-compatible | `http://127.0.0.1:1234/v1` | Local or hosted OpenAI-compatible chat/vision |
| Ollama | `http://127.0.0.1:11434` | Local chat; image input when the selected model supports it |
| OpenAI | `https://api.openai.com/v1` | Select OpenAI-compatible and use `OPENAI_API_KEY` |
| Anthropic | your Messages API base | Uses `ANTHROPIC_API_KEY` when configured as the key environment |

Keys are read only at runtime from the configured environment variable or `.env` file. The default optional file is `G:\private\.env.openai`. The installer, logs and ZIP never contain a key.

## Diagnostics and removal

- Run **`DIAGNOSE_Barros_AI.bat`** after launching once. It checks the target, loader, plugin, private runtime, backend tests and BepInEx log evidence.
- BepInEx log: `S:\Unity_Games\PC3 - Pizza Creator\BepInEx\LogOutput.log`
- Backend history: `S:\Unity_Games\PC3 - Pizza Creator\BarrosAI\backend\data\conversation_history.json`
- Run **`UNINSTALL_Barros_AI_Designer.bat`** to remove only this plugin and its sidecar. It leaves game assemblies, saves and shared BepInEx files untouched.

## Compatibility boundary

This release was built directly against the supplied Unity 2017.3.1p4 x64 files and decompiled interfaces. The backend and catalog paths are automated and tested in this package. The final live-scene smoke test must occur on Windows because Unity's native player, microphone and renderer cannot execute in this Linux workspace. The diagnostic script records that proof without changing the game.

See `docs/ARCHITECTURE.md`, `docs/REVERSE_ENGINEERING_EVIDENCE.md`, `docs/UI_MOCKUP_MAPPING.md`, `docs/RUNTIME_ACCEPTANCE.md`, and `CLAUDE_HANDOFF.md` for exact implementation evidence.
