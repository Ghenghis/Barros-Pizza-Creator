# Barro's Pizza Creator Chat UI — Slice 2 Design

> **SCOPE LOCK — PC3 + Barro's Pizza ONLY.**
> This project targets **Barro's Pizza** (rebranded from "Pizza Connection 3 — Pizza Creator", PC3) exclusively.
> **PC2 (Fast Food Tycoon 2 / Pizza Creator 2) is PROHIBITED.**
> Working directory: `S:\Unity_Games\PC3 - Pizza Creator\creator-ui\`. Forbidden paths: `S:\Barro's-Pizza*` (PC2).

**Status:** Design approved (user directive 2026-08-25)
**Scope:** In-game chat UI overlay — 4 chat modes + Name-this-pizza dialog + sidebar tab nav. Built in a separate Unity reconstruction project (Unity UI Toolkit). Apply recipe writes `pizza.final.json` for the existing M0–M5 conversion harness to ingest.

## Background & motivation

The user owns **Barro's Pizza** (formerly Pizza Connection 3 — Pizza Creator, Unity 2017-era Mono build). Slice 1 of `_pizza-agent` shipped the offline composer/renderer/verifier backend. Slice 2 is the in-game chat UI: an extra tab inside the existing Pizza Nonamo right panel that hosts 4 chat modes (Chef Voice, Barro's Design Crew, AI Pizza Lab, Barro's AI Pizza Designer).

The user shared 8 mockups as the truth spec. This Slice 2 build must recreate the 4 chat panels + Name-this-pizza dialog at ≥98% pixel accuracy (truth proof snapshots). Existing Bakehouse/Ingredient tabs are NOT rebuilt — they remain in the original game. Chat modes write `pizza.final.json` matching PC3's PizzaModel DataContract; in-game ingredient placement is the conversion harness's job.

## Goals

1. **Render 4 chat modes** (Chef Voice, Barro's Design Crew, AI Pizza Lab, Barro's AI Pizza Designer) as Unity UI Toolkit panels inside a separate reconstruction project.
2. **Sidebar tab nav** — 4 chat-mode icons that switch between panels (visual stub; no actual switching to existing Bakehouse/Ingredient tabs).
3. **Name-this-pizza dialog** — appears after Apply; user types name, Continue saves `pizza.recipe.json` + `pizza.final.json`.
4. **LLM-driven chat** — LMStudio primary (localhost:1234), OpenAI fallback. Each mode has its own system prompt and persona.
5. **Apply recipe** — writes `pizza.final.json` matching PC3 PizzaModel DataContract, ready for the existing M0–M5 conversion harness to ingest (no live Unity editing in this Slice).
6. **Truth proof** — every panel renders ≥98% pixel match against its mockup (pixelmatch in CI). Hard floor 93%.

## Non-goals (out of scope for this Slice)

- Real voice input/output (mic button is visual-only; text input is the real interaction)
- Live Unity ingredient placement when "Apply" is clicked (handoff to conversion harness)
- Rebuilding existing Bakehouse / Ingredient / Recipe-book tabs (those remain in the original game)
- Saving to actual in-game save files (handoff to conversion harness)
- Multi-language support (en-GB/AU TTS per HANDOVER — deferred entirely)
- Touch / mobile interaction (desktop Unity Editor + standalone build only)

## Architecture

3 layers, file-based handoff matching Slice 1:

```
┌──────────────────────────────────────────────────────────────┐
│  PRESENTATION (Unity UI Toolkit, reconstruction project)     │
│  - UXML/USS for each chat panel (ChefVoice, Crew, Lab, Designer, NameDialog)
│  - VisualElement tree, USS classes match mockup exactly
│  - C# MonoBehaviour controllers bind UXML ↔ data
│  - Sidebar tab nav (VisualElement icons, no real switching to existing tabs)
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼  (calls via HTTP)
┌──────────────────────────────────────────────────────────────┐
│  ORCHESTRATION (C# in reconstruction project)                │
│  - ChatModeController (state per mode, message history)
│  - LLMClient (HTTP to LMStudio :1234, fallback OpenAI)
│  - RecipeComposer (reuses Slice 1 schemas via JSON contract)
│  - ScoringEngine (taste/cost/profit/novelty, same formulas as Slice 1)
│  - JsonExporter (writes pizza.final.json matching PC3 PizzaModel DataContract)
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼  (writes file)
┌──────────────────────────────────────────────────────────────┐
│  PERSISTENCE (file system)                                    │
│  - pizza.recipe.json (intermediate, Slice 1 format)          │
│  - pizza.final.json (PC3 DataContract JSON, ready for M1)    │
│  - chat-history-{mode}.json (per-mode conversation log)      │
│  - evidence/snapshots/{timestamp}-{panel}.png (verification)
└──────────────────────────────────────────────────────────────┘
```

### Reconstruction project layout

```
S:\Unity_Games\PC3 - Pizza Creator\creator-ui\
├── Assets\
│   ├── Scenes\CreatorUI.unity              # Main scene with chat panel
│   ├── UI\
│   │   ├── Panels\ChefVoice.uxml + .uss
│   │   ├── Panels\Crew.uxml + .uss
│   │   ├── Panels\Lab.uxml + .uss
│   │   ├── Panels\Designer.uxml + .uss
│   │   ├── Panels\NameDialog.uxml + .uss
│   │   ├── Sidebar\SidebarTabs.uxml + .uss
│   │   └── Shared\Buttons.uss, Cards.uss, Theme.uss
│   ├── Scripts\
│   │   ├── Chat\ChatModeController.cs
│   │   ├── Chat\ChefVoicePanel.cs
│   │   ├── Chat\CrewPanel.cs
│   │   ├── Chat\LabPanel.cs
│   │   ├── Chat\DesignerPanel.cs
│   │   ├── Chat\NameDialog.cs
│   │   ├── LLM\LLMClient.cs
│   │   ├── LLM\LMStudioBackend.cs
│   │   ├── LLM\OpenAIBackend.cs
│   │   ├── Recipe\RecipeComposer.cs
│   │   ├── Recipe\ScoringEngine.cs
│   │   ├── Recipe\JsonExporter.cs
│   │   └── Sidebar\TabNavigator.cs
│   └── StreamingAssets\catalog.json         # Slice 1 ingredient catalog (read-only)
├── ProjectSettings\Packages\manifest.json   # com.unity.modules.uielements
├── docs\superpowers\specs\                  # design (this file)
├── docs\superpowers\plans\                  # implementation plan
├── docs\mockups\                             # truth spec images
├── evidence\snapshots\                       # verification screenshots
├── tests\                                      # PlayMode + EditMode tests
└── README.md
```

### Mockup-as-source-of-truth workflow

1. Open mockup image (e.g., `docs/mockups/ChefVoice.png`)
2. Extract exact hex colors, font sizes, spacing → `Shared/Theme.uss`
3. Layout each panel in UXML matching mockup pixel grid
4. Render in Unity Editor → screenshot
5. `pixelmatch(mockup, screenshot)` → truth proof
6. Iterate until ≥98% match

## Components

### 4 chat panels

| Panel | UXML | MonoBehaviour | Mockup |
|---|---|---|---|
| ChefVoice | `ChefVoice.uxml` | `ChefVoicePanel.cs` | `docs/mockups/01-chef-voice.png` |
| Crew | `Crew.uxml` | `CrewPanel.cs` | `docs/mockups/02-crew.png` |
| Lab | `Lab.uxml` | `LabPanel.cs` | `docs/mockups/03-lab.png` |
| Designer | `Designer.uxml` | `DesignerPanel.cs` | `docs/mockups/04-designer.png` |

### Common panel features

- Chat history scroll view (User/AI message bubbles with timestamps)
- AI Recipe Draft / Recipe card (recipe name, ingredient list, score bars)
- Heat / Surprise / Build action buttons (mode-specific)
- Apply button → triggers NameDialog

### Per-panel unique features

- **ChefVoice:** mic waveform animation (animated VisualElement, no audio capture); heat selector (Mild/Medium/Hot)
- **Crew:** 4 agent rows with consensus bars (Flavor/Profit/Popularity/Originality); crew discussion log
- **Lab:** "What should I invent?" tag chips; Surprise me button; recipe card list (multiple ranked candidates); autopilot toggle
- **Designer:** Build/Surprise/Improve tab strip; chat input + AI response; recipe card with score display; action buttons (Try 3 versions, Balance flavor, Lower cost)

### NameDialog

- Modal overlay
- Text input with "Pizza Nonamo" placeholder
- Continue / Cancel buttons
- Continue: writes `output/{name}.recipe.json` + `output/{name}.final.json`

### Sidebar tabs

- 4 chat-mode icons (visual stub)
- Switching icons swaps which chat panel is visible
- Does NOT switch to Bakehouse/Ingredient tabs (those are in original game)

### Shared USS classes

- `Buttons` (Primary, Secondary, Chip, Tag)
- `Cards` (RecipeDraft, RecipeCard, CrewMember)
- `Bars` (ScoreBar)
- `Theme` (`--color-bg`, `--color-accent`, `--font-display`)

## Data Flow

```
User types in chat input
  → ChatModeController.SendMessage(text)
    → LLMClient.Complete(prompt, system, mode)
      → LMStudioBackend.POST(:1234/v1/chat/completions) [primary]
        → on 5xx/timeout → OpenAIBackend.POST(api.openai.com) [fallback]
      → returns Recipe JSON
    → RecipeComposer.ValidateAndRepair(recipe)
      → uses catalog.json (StreamingAssets, from Slice 1)
      → applies Slice 1 solver rules (IDs, amounts, positions, count)
    → ScoringEngine.Compute(recipe)
      → taste/cost/profit/novelty (same formulas as Slice 1)
    → JsonExporter.WriteFinal(pizza, recipePath)
      → writes pizza.final.json in PC3 PizzaModel DataContract shape
    → ChatPanel.UpdateUI(recipe, scores)
      → renders RecipeDraft card + score bars

Apply recipe button
  → JsonExporter.PromptForName()
    → NameDialog opens
    → user types name, hits Continue
    → pizza.recipe.json saved to {projectRoot}/output/{name}.recipe.json
    → pizza.final.json saved to {projectRoot}/output/{name}.final.json
    → chat panel shows "Recipe '{name}' saved. Ready for M1 conversion harness."
```

### State

`ChatSession` (per mode): `mode`, `messages[]`, `currentRecipe`, `status` (`Idle` | `Composing` | `Rendered` | `Saved`)

## Error Handling

| Failure | Behavior |
|---|---|
| LMStudio unreachable (timeout 5s) | Auto-fallback to OpenAI; log warning with mask_key |
| OpenAI key missing | Show error in chat: "No LLM backend available. Set OPENAI_API_KEY or start LMStudio." |
| LLM returns invalid JSON | Retry once with stricter prompt; on second failure, show error in chat |
| Catalog.json missing | Show error: "Run `pizza-agent extract-ingredients` first to generate catalog" |
| Recipe fails Slice 1 validation | Show validation errors in chat; offer "Edit manually" button (future) |
| Apply recipe → no name | Force user to name via dialog (Cancel returns to chat) |
| Snapshot verification < 98% | Block PR; show diff image highlighting mismatched regions |
| Reconstruction project doesn't open | Show "Run from Unity Editor 2022 LTS or later" error |

## Testing

### EditMode tests (`tests/EditMode/`)

- `LLMClientTests` — mock HTTP, verify retry, fallback, key masking
- `RecipeComposerTests` — Slice 1 schema compatibility, solver repair
- `ScoringEngineTests` — taste/cost/profit/novelty formulas match Slice 1
- `JsonExporterTests` — PC3 DataContract shape verified against Slice 1 `samples/good_pizza.json`

### PlayMode tests (`tests/PlayMode/`)

- `PanelLayoutTests` — each panel renders without exceptions
- `TabNavigationTests` — sidebar switches between chat modes
- `NameDialogTests` — input + Continue/Cancel

### Snapshot tests (`tests/Snapshots/`)

- `pixelmatch(mockup, screenshot)` per panel, ≥98% match required
- Run on every commit; CI blocks merge below threshold
- Mockups live in `docs/mockups/` as the truth source

### HermesProof evidence

- Every snapshot test writes `{timestamp}-{panel}.png` to `evidence/snapshots/`
- Every LLM call appends redacted entry to evidence ledger
- Per-task evidence entries via `hermes_append_evidence`

## Critical decisions / things to know

### 1. Unity version

Reconstruction project targets Unity **2022 LTS** (or 2023 LTS if 2022 is unavailable on this machine). UI Toolkit is stable in both. The original 2017 build is NOT modified — this is enforced by the SCOPE contract on the existing `pizza-agent-slice1-contract`.

### 2. PC3 PizzaModel DataContract shape (canonical)

`pizza.final.json` MUST match Slice 1's `samples/good_pizza.json` exactly. The .NET verifier in Slice 1 will load it via `DataContractJsonSerializer`. Ingredient size enum: `{ Large=0, Medium=1, Small=2 }`. Price formula: `(amount_g / 100) * base_price`.

### 3. Slice 1 contract reuse

`composer.py` / `solver.py` / `scoring.py` from Slice 1 are Python and won't be re-implemented in C#. Instead, `RecipeComposer.cs` reads the same JSON contracts and applies the same rules. The Slice 1 sample files (`samples/good_pizza.json`, `samples/bad_*.json`) are imported into `tests/Snapshots/` as the truth source for `JsonExporter` tests.

### 4. Mockup extraction

Mockup images live in `docs/mockups/`. The exact dimensions and colors are extracted by visual inspection + a small color-picker utility (no need for automated extraction). Each panel's UXML uses absolute pixel positions matching the mockup.

### 5. Sidebar tab switching

The sidebar shows 4 chat-mode icons only. Switching between Bakehouse/Ingredient tabs (the original game's UI) is out of scope — those tabs remain in the original game. The reconstruction project's sidebar is purely visual for the 4 chat modes.

### 6. Voice deferred

The mic button in ChefVoice mode animates (waveform pulses when "listening") but no audio is captured or played. A future Slice can add WebRTC or Azure Speech. For now, users type prompts.

### 7. Apply → JSON → conversion harness handoff

"Apply recipe" writes `pizza.final.json` matching the PC3 DataContract. The existing `PC3_Barros_Conversion_Harness_v0.1/scripts/apply_pack.py` is what actually places ingredients in the game (separate Slice, not this one).

## Known limitations

- **Reconstruction project is visual-only.** Running the .exe won't render text on a real GPU (no font assets shipped). Tests run in Unity Editor via PlayMode.
- **No real Unity game state integration.** "Apply recipe" produces JSON; in-game placement is the conversion harness's job.
- **Sidebar tabs don't switch to existing game tabs.** This is intentional — out of scope for this Slice.
- **Voice is a visual mock.** Real STT/TTS deferred.
- **Recipe edits after Apply not supported.** "Edit manually" button shows but does nothing.

## NOT done (deferred to future Slices)

- Voice STT/TTS (real audio)
- Multi-language (en-GB/en-AU Azure TTS per HANDOVER)
- "Edit manually" recipe editor
- Live Unity ingredient placement (instead of JSON handoff)
- Real-time game state sync (read what player has open in PizzaCreator scene)
- Sidebar tabs that actually switch to existing Bakehouse/Ingredient tabs

## How to continue (for future sessions)

1. Read this file and `docs/superpowers/plans/2026-08-25-barros-creator-chat-ui.md`
2. Open `creator-ui/` in Unity 2022 LTS
3. Run `tests/EditMode/` + `tests/PlayMode/` to verify health
4. Run `tests/Snapshots/` to verify ≥98% pixel match against mockups
5. For new features, add to this spec then implement

## Git history (planned)

Fresh `creator-ui/` repo. Commit cadence:
- `chore: scaffold creator-ui/ Unity 2022 LTS reconstruction project`
- `feat(ui): add Sidebar tabs + shared USS Theme + Buttons/Cards/Bars classes`
- `feat(chat): ChefVoice panel + ChefVoicePanel controller`
- `feat(chat): Crew panel + 4 agent personas`
- `feat(chat): Lab panel + batch ranking + autopilot`
- `feat(chat): Designer panel + Build/Surprise/Improve tabs`
- `feat(dialog): NameDialog + Apply → JSON handoff`
- `feat(llm): LLMClient + LMStudio backend (localhost:1234) + OpenAI fallback`
- `feat(recipe): RecipeComposer (Slice 1 schema reuse) + ScoringEngine + JsonExporter`
- `test(snapshot): pixelmatch ≥98% per panel + CI threshold`
- `test(editmode): LLMClient + RecipeComposer + ScoringEngine + JsonExporter unit tests`
- `test(playmode): PanelLayout + TabNavigation + NameDialog`

Each commit appends evidence via HermesProof `hermes_append_evidence`.

## Credits

Designed for Claude (Sonnet 4.5) implementation. Coordinated with HermesProof. Mockups by user.
