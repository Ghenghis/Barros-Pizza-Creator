# SCOPE: PC3 PIZZA CREATOR ONLY — Claude Method/File Implementation Atlas

**Owner:** Claude  
**Repository:** `Ghenghis/Barros-Pizza-Creator`  
**Runtime profile:** `creator-0.11.272`  
**Purpose:** remove codebase rediscovery. Open the named file/method, make the smallest correct change, retain the named proof, then move to the next gate.

This atlas does **not** authorize Studio or Workbench edits. Runtime Proof Studio and Barro's Workbench remain ChatGPT-owned workstreams.

## 1. Current Creator code anchors

| Concern | File | Current anchor | Use it for |
|---|---|---|---|
| Plugin lifecycle / exact process / F9 | `plugin-src/BarrosAiPlugin.cs` | `Awake()`, `Update()`, `StartBackend()` | BepInEx load, service injection, tab-install loop, reload verification |
| Native game model bridge | `plugin-src/GameBridge.cs` | `BuildCatalog()`, `Prepare()`, `Preview()`, `Apply()`, `Restore()`, `SaveCurrentToRecipeBook()`, `VerifyLastSavedReload()`, `BuildModel()`, `ScoreWithGame()` | all real PizzaModel behavior |
| Fifth-tab creation | `plugin-src/RuntimeTabInstaller.cs` | `TryInstall()`, `Activate()`, `PlaceAfterExistingTabs()`, `FindHeader()`, `CreateHeaderBanner()` | UI-301/302/303 |
| Four-mode UI / operator actions / mic / F8 | `plugin-src/PanelRenderer.cs` | `Configure()`, `OnEnable()`, `OnDisable()`, `Update()`, `SetMode()`, action callbacks, voice methods | Chat/Lab/Crew/Voice, F8, Preview/Apply/Restore/Save, mic/STT |
| Plugin-side JSON contract | `plugin-src/Models.cs` | `AiRecipe`, `AiRecipeIngredient`, request/response DTOs | exact pizza-agent -> native bridge contract |
| Sidecar HTTP transport | `plugin-src/BackendClient.cs` | `Compose()`, `Transcribe()`, `Health()`, `History()`, `Post<>()` | existing Creator sidecar; do not create a competing transport |
| Runtime evidence | `plugin-src/EvidenceRecorder.cs` | `Record()`, `Capture()` | retained `runtime-events.jsonl` + screenshots |
| Main-thread callback bridge | `plugin-src/MainThreadDispatcher.cs` | dispatcher queue | UI-safe backend callbacks |
| Voice WAV encoding | `plugin-src/WavEncoder.cs` | WAV conversion | VOX-501/502 |
| Release truth | `contracts/rc1.acceptance.json` | L0-L6 gates | only source of certification truth |
| Proof execution | `scripts/Invoke-ProofContract.ps1` | Static/Build/Runtime/All | retained gate promotion |

## 2. The most important current convergence gap

The current `AiRecipeIngredient` DTO in `plugin-src/Models.cs` contains:

- `id`
- `size`
- `target_grams`
- `distribution`
- `note`
- `repaired_from`

It does **not** currently carry explicit per-piece position/rotation records.

The current `GameBridge.BuildModel()` therefore derives piece count from `target_grams / ingredient.Amount` and generates positions through `PositionFor(...)`.

That is a useful existing implementation, but it is the exact place where the completed `_pizza-agent` final interchange must converge with the native contract if Slice 1 now produces validated placement/rotation data.

### Required direction

Do **not** create a second native bridge.

Evolve the existing DTO/bridge so the verified final payload can become the same `PizzaModel` used by Preview/Apply/Save/reload.

Preferred compatibility strategy:

1. Keep the existing high-level ingredient fields for backward compatibility.
2. Add a versioned explicit placement representation only if the pizza-agent final schema requires it.
3. In `GameBridge.BuildModel()`, prefer verified explicit placements when supplied.
4. Use the existing deterministic `PositionFor()` route only for payloads that legitimately have no explicit placement contract.
5. Never silently discard a verifier-approved position/rotation and generate a different one.
6. Preserve exact ingredient ID, size, amount semantics, shape, profit factor, position, and rotation through Python -> JSON -> C# -> native model.

## 3. CLD-101 — exact file-level route for final JSON/native alignment

### Open first

- `_pizza-agent` final schema / serializer files in Claude's isolated Creator workspace.
- `plugin-src/Models.cs`
- `plugin-src/GameBridge.cs`
- existing .NET verifier tests
- existing Python final-output tests

### Change only what is needed

#### `plugin-src/Models.cs`

If explicit placements exist in `pizza.final.json`, introduce a DTO that represents **only fields the verifier actually produces**, for example conceptually:

```text
ingredient id
size
position x/y/z
rotation x/y/z
```

Do not invent unused fields. Keep JSON names synchronized with the pizza-agent schema.

#### `plugin-src/GameBridge.cs`

Primary hotspot: `BuildModel(AiRecipe recipe)`.

Implementation order:

1. `new PizzaModel()` + `Bind()` remains.
2. Preserve safe recipe ID/name.
3. Preserve verified profit factor.
4. Fetch shape using `database.GetPizzaShape(...)` and copy `DoughPositions`.
5. For each verified ingredient placement:
   - resolve exact installed ingredient by ID + real size;
   - reject/skip only according to the verifier contract, never by guessing aliases here;
   - bind a real `PizzaModel.IngredientContainerModel`;
   - bind the real size-specific `IngredientModel`;
   - assign the verifier-approved position and rotation;
   - add it to `model.ingredients`.
6. Calculate native costs.
7. `ScoreWithGame()` remains the native score authority when game services are available.

### Cross-contract test

Create one deterministic fixture that travels through all three stages:

```text
pizza-agent final JSON
  -> .NET verifier
  -> Creator plugin DTO
  -> GameBridge model mapping test/inspection
```

Assert exact agreement for:

- name
- shape
- ingredient IDs
- size values (`Large=0`, `Medium=1`, `Small=2`)
- placement count
- position values
- rotation values
- profit factor

Do not treat matching aggregate grams as sufficient when explicit placements are part of the final contract.

## 4. CLD-102 — sidecar integration: do not rebuild networking

The plugin already owns an HTTP transport in `plugin-src/BackendClient.cs`.

Existing anchors:

- `Compose(endpoint, request, callback)`
- `Transcribe(wav, callback)` -> `/transcribe`
- `Health(...)` -> `/health`
- `History(...)` -> `/history`
- generic `Post<TRequest,TResponse>()`

Therefore the skip-ahead rule is:

> adapt pizza-agent behind the existing Creator sidecar/API contract; do not create a second in-game HTTP client or second service port unless a verified incompatibility requires it.

The BepInEx plugin already defaults to `http://127.0.0.1:48173` in `BarrosAiPlugin.Awake()` and can auto-start `BarrosAI/backend/main.py`.

### Acceptance path

1. Existing UI sends request through `BackendClient`.
2. Existing sidecar invokes/adapts pizza-agent.
3. Sidecar returns validated `AiResponse`/recipe payload.
4. UI calls `game.Prepare()` / `game.Preview()` only after valid response.
5. Errors remain explicit; no fabricated recipe on verifier/provider failure.

## 5. CLD-201 — fifth tab and four modes: edit the existing live UI

### Tab creation

`plugin-src/RuntimeTabInstaller.cs::TryInstall()` already:

- locates the live `PizzaCreatorTabBar`;
- clones recipe-tab geometry/style;
- creates the AI tab/content;
- calls `tabBar.RegisterTab(aiTab)`;
- creates the Barro's header banner;
- attaches `PanelRenderer`;
- records `ui.tab_installed` and header-fit evidence.

Do not replace this with a new windowing system.

### Mode UI

`plugin-src/PanelRenderer.cs` already owns `DesignerMode.Chat/Lab/Crew/Voice` and `SetMode()`.

Polish/fix the existing renderer until the four live references are satisfied.

### UI proof events/files

Existing evidence root is created by `EvidenceRecorder` under:

```text
<GameRoot>\BarrosAI\evidence\
  runtime-events.jsonl
  screenshots\
```

Expected UI proof names include:

- `ui-tab.png`
- `ui-header.png`
- `ui-stock-header.png`
- `chat.png`
- `lab.png`
- `crew.png`
- `voice.png`

`PanelRenderer.Update()` already maps F8 to the active mode capture. Do not create a second screenshot hotkey path.

## 6. CLD-301 — Preview / Restore / Apply already have the right native seam

Open `plugin-src/GameBridge.cs`.

### Preview

`Preview(AiRecipe recipe)` currently:

1. captures restore point;
2. prepares candidate if needed;
3. calls `pizzaCreator.LoadPizzaFromModel(lastCandidate)`;
4. records `action.preview.success`.

Keep this seam. Fix model fidelity upstream rather than replacing Preview.

### Restore

`Restore()` reloads the captured `restorePoint` through the same native service and records `action.restore.success`.

### Apply

`Apply()` loads the candidate, clears the restore point, and records `action.apply.success`.

### UI wiring

`PanelRenderer` already calls `game.Preview(recipe)` and `game.Apply(recipe)` from live controls. Connect/fix Restore/Save controls in this same class rather than creating external tooling.

## 7. CLD-302 — Native save/reload/export proof is implemented in v1.2 RC2

Open:

- `plugin-src/GameBridge.cs`
- `plugin-src/BarrosAiPlugin.cs`
- `plugin-src/EvidenceRecorder.cs`

`GameBridge.SaveCurrentToRecipeBook()` uses native `SaveCurrentPizzaToRecipes()`, checks the returned native recipe model, and requires a non-empty JSON file under `Paths.recipes`.

`GameBridge.ExportCurrentJpeg()` resolves the one scene-local stock `ScreenshotButton`, preserves its `specialScreenshotUI` transition, invokes its referenced `ScreenCapture.Capture` method, restores prior UI state, and validates the written JPG stream. Do not replace it with an independent encoder.

`GameBridge.VerifyLastSavedReload()` already builds an exact signature containing:

- ID/name
- profit factor
- dough positions
- ingredient ID
- size
- position
- rotation

`BarrosAiPlugin.Update()` binds F9 to `ReloadLastSaved()`. The bridge reads the persisted JSON through PC3's `ISerializerService`, resolves ingredient references through `IDatabaseService`, requests the native event-driven load, then calls the verifier and records:

- `action.reload.verified`, or
- `action.reload.failed`

and captures `reload.png` on success.

### Claude's job here

Do not redesign reload/export verification. Run the exact Windows gates and retain the persisted JSON, JPG, hashes, logs, and `reload.png` evidence.

## 8. CLD-401 — Chef Voice is an integration/verification task, not a greenfield task

Open:

- `plugin-src/PanelRenderer.cs`
- `plugin-src/WavEncoder.cs`
- `plugin-src/BackendClient.cs`

The live UI already has microphone state and calls the existing voice path. `PanelRenderer`:

- starts/stops Unity `Microphone` capture;
- limits recording duration;
- converts the captured clip to WAV;
- calls `backend.Transcribe(wav, ...)`;
- rejects empty/failed transcription;
- copies the transcript into `prompt`;
- records `voice.transcription.success`;
- submits the transcript through the normal chat recipe path.

`BackendClient.Transcribe()` already posts to `/transcribe`.

Therefore focus on:

1. real Windows device enumeration/capture;
2. non-empty PCM/WAV;
3. configured provider success;
4. retained non-secret evidence;
5. live Voice screenshot.

Do not replace working Unity mic/WAV/client layers merely to change STT providers.

## 9. CLD-501 — exact runtime loader proof anchors

Open `plugin-src/BarrosAiPlugin.cs`.

Settled runtime sequence:

```text
BepInEx discovers BarrosAiPlugin
  -> Awake()
  -> EvidenceRecorder created
  -> GameBridge + BackendClient created
  -> optional sidecar startup
  -> Update() waits for Kernel
  -> Zenject injects GameBridge
  -> RuntimeTabInstaller created
  -> TryInstall() repeats until live PizzaCreatorTabBar exists
```

Proof must come from the actual target process/log, not this source path.

Relevant release gates:

- BLD-101..104
- RUN-201
- RUN-202

If exact assembly hashes differ, stop certification.

## 10. CLD-601 — four F8 modes require no new capture subsystem

`PanelRenderer.Update()` already does:

```text
F8 -> EvidenceRecorder.Capture(ModeFileName())
```

`ModeFileName()` maps to `chat`, `lab`, `crew`, `voice`.

Claude should spend effort on **live geometry/content parity**, then press F8 in each final state and run the existing comparison harness.

## 11. CLD-701 — proof promotion path

Do not hand-edit gate states.

Final Creator path:

```text
scripts/Invoke-ProofContract.ps1
  -Stage All
  -RequireComplete
  -GameRoot "S:\Unity_Games\PC3 - Pizza Creator"
```

Only after the retained result is complete may `/proof/latest` report runtime certification.

## 12. Smallest-diff implementation order

Use this order to reduce rework:

1. Update/version final interchange schema only if needed.
2. Update `Models.cs` DTOs to match it exactly.
3. Update `GameBridge.BuildModel()` to consume verified placement data.
4. Add cross-language fixture/test.
5. Adapt existing sidecar to pizza-agent; leave `BackendClient` protocol stable where possible.
6. Run portable tests/build.
7. Finish/polish existing fifth-tab modes.
8. Exercise Preview/Restore/Apply against the exact model.
9. Exercise Save/native reload/F9.
10. Exercise real mic/STT.
11. Capture F8 modes.
12. Run All-stage proof.
13. Hand retained evidence to ChatGPT; do not edit Studio/Workbench.

## 13. Failure routing — fix the producer, not the consumer

| Symptom | First file/workstream to inspect |
|---|---|
| Wrong ingredient/placement after Preview | `Models.cs` + `GameBridge.BuildModel()` + pizza-agent final schema |
| Correct JSON but verifier rejects | pizza-agent/verifier contract, not UI |
| Verifier passes but sidecar response malformed | Creator backend adapter/API |
| Tab absent | `BarrosAiPlugin.Update()` injection/install loop + `RuntimeTabInstaller.TryInstall()` |
| Tab exists but layout wrong | `RuntimeTabInstaller` geometry + `PanelRenderer` |
| Preview works, Restore wrong | `GameBridge.CaptureRestorePoint()` / `Restore()` |
| Apply works, saved reload mismatch | `SaveCurrentToRecipeBook()` / native operator reload / `VerifyLastSavedReload()` |
| Mic captures nothing | `PanelRenderer` Unity Microphone path/device/runtime |
| Mic works, transcription fails | sidecar `/transcribe` provider path |
| F8 missing | `PanelRenderer.Update()` + `EvidenceRecorder.Capture()` |
| Screenshot requested but file not present | evidence filesystem/capture completion; do not call it PASS |
| Proof says NOT_RUN | execute the gate; do not weaken contract |

## 14. Hard no-go list

- Do not add Studio implementation here.
- Do not add Workbench implementation here.
- Do not create a second native pizza model authority.
- Do not create a second in-game AI tab/window if the existing tab route can be fixed.
- Do not create a second screenshot/evidence subsystem.
- Do not treat `screenshot.requested` as proof that the PNG exists; verify retained file.
- Do not infer runtime success from source/build success.
- Do not expose credentials in logs/evidence.
- Do not use material outside the locked PC3 scope.

## 15. Copy/paste continuation prompt for Claude

```text
Continue PC3 Pizza Creator only. Read 00_READ_FIRST_PC3_ONLY.md, CLAUDE_HANDOFF.md, docs/CLAUDE_SKIP_AHEAD_RUNTIME_IMPLEMENTATION_PACKET.md, and docs/CLAUDE_METHOD_FILE_IMPLEMENTATION_ATLAS.md first. Do not re-audit settled architecture. Work from the existing code anchors.

Highest priority: converge the completed pizza-agent final JSON/verifier contract into plugin-src/Models.cs and GameBridge.BuildModel() so verifier-approved ingredient IDs, sizes, positions, rotations, shape and profit factor become the exact real PizzaModel used by Preview/Apply/Save/reload. Do not create a second bridge or networking stack. Preserve existing BackendClient, RuntimeTabInstaller, PanelRenderer, EvidenceRecorder and proof-harness architecture unless a demonstrated defect requires a focused fix.

Then proceed through fifth-tab live UI, Preview/Restore/Apply, native Save + F9 exact reload, real mic/STT, four F8 captures, and All-stage RequireComplete proof. Retain evidence for every promoted gate. Never claim runtime success from source or CI. Do not modify Runtime Proof Studio or Barro's Workbench; hand shared evidence/schema deltas to ChatGPT instead.
```
