# SCOPE: PC3 PIZZA CREATOR ONLY — Claude Skip-Ahead Runtime Implementation Packet

**Owner:** Claude  
**Repository:** `Ghenghis/Barros-Pizza-Creator`  
**Runtime profile:** `creator-0.11.272`  
**Purpose:** eliminate rediscovery and move directly from the completed Slice-1 backend into the real Pizza Creator runtime path.

This file is an implementation accelerator, not a substitute for retained proof. `contracts/rc1.acceptance.json` remains the release truth source.

## 1. Read these first, then stop researching architecture

Read once at session start:

1. `00_READ_FIRST_PC3_ONLY.md`
2. `CLAUDE_HANDOFF.md`
3. `CLAUDE_ACCESS_MAP_PC3_CREATOR.md`
4. `CLAUDE_NEXT_TASKS_PC3_CREATOR.md`
5. `contracts/claude-creator-task-queue.json`
6. `contracts/rc1.acceptance.json`

After those files agree with the checkout, do not spend another exploration pass rediscovering the following settled facts.

## 2. Settled native facts — use them as constants of the plan

- Creator target is the exact `creator-0.11.272` build.
- Unity target is `2017.3.1p4 x64`.
- The Creator catalog is exactly **87** valid ingredient IDs in six categories.
- Ingredient amounts are grams.
- `IngredientSize`: `Large=0`, `Medium=1`, `Small=2`.
- Shapes are Round, Square, Star, Triangle.
- Shape placement authority is `IDatabaseService.GetPizzaShape(shapeId).DoughPositions`.
- Do not synthesize a unit-circle dough model.
- A valid native recipe is represented by a real `PizzaModel` with dough positions and bound `IngredientContainerModel` / size-specific `IngredientModel` instances.
- `IPizzaCreatorService.LoadPizzaFromModel(PizzaModel)` is the native Preview/Apply bridge.
- Native price/cost and citizen taste/price scoring remain game authority when available.
- `TabBar.RegisterTab(Tab)` is the real fifth-tab registration route.
- BepInEx 5 x64 is the preferred runtime integration route; do not replace the main game assembly merely to add the AI tab.
- The stock 3D pizza composer is the renderer. A generated flat image is not a substitute for native ingredient placement.
- Unified AI modes: **Chat / AI Lab / Design Crew / Chef Voice**.
- F8 is the canonical live screenshot capture for the active AI mode.
- F9/equivalent exact reload comparison must validate real modeled state after native recipe-book reload.

## 3. Convergence architecture — there must be only one recipe authority

The implementation should converge to this flow:

```text
user prompt / voice
    -> existing Creator sidecar/provider routing
    -> pizza-agent compose
    -> deterministic schema validation
    -> .NET/native verifier
    -> validated recipe payload
    -> BepInEx Creator bridge
    -> real PizzaModel
    -> IPizzaCreatorService.LoadPizzaFromModel
    -> stock 3D pizza composer
```

Rules:

- Python proposes; the native game validates/owns IDs, model semantics, price/cost, and runtime state.
- The .NET verifier must reject incompatible payloads before native actions run.
- Do not create a second sidecar, second UI product, second recipe database, or second scoring authority.
- Preserve the existing Creator API surface: `/health`, `/history`, `/proof/latest`, `/inspect-attachment`, `/compose`, `/chat`, `/lab`, `/crew`, `/transcribe`, `/reload`, `/shutdown`.

## 4. CLD-101 — final JSON to native contract: exact implementation recipe

Do this before additional UI work.

### Required semantic fields

The existing `pizza.final.json` representation must carry enough information to deterministically reconstruct:

- recipe identity/name;
- exact shape ID;
- exact valid ingredient ID;
- amount in grams;
- exact `IngredientSize` numeric value;
- per-placement position;
- per-placement rotation;
- profit factor only where the native contract expects it.

Do **not** invent alternate size numbers or alternate shape geometry.

### Adapter algorithm

1. Parse final JSON.
2. Validate shape ID against the real Creator shape set.
3. Resolve the shape through the native database and copy its `DoughPositions`.
4. Validate every ingredient ID against the exact 87-item catalog.
5. Validate amount is finite, non-negative and expressed in grams.
6. Validate size is one of `0,1,2` with native meaning Large/Medium/Small.
7. Validate every placement contains finite position and rotation values.
8. Build the native `PizzaModel`.
9. For each ingredient placement, bind the correct `IngredientContainerModel` and the size-specific `IngredientModel`.
10. Preserve recipe identity and profit factor expected by the game.
11. Run the .NET/native verifier.
12. Only return a recipe to the UI when the verifier says it is suitable for the native bridge.

### Cross-check fixture

Add one deterministic fixture that proves all three layers agree:

```text
Python final JSON
    == semantic identity ==
.NET verifier interpretation
    == semantic identity ==
Creator bridge input
```

Compare at minimum: recipe ID/name, shape, ingredient IDs, grams, size enum, placement count, position and rotation.

A mismatch is a hard failure, never an automatic conversion.

## 5. CLD-102 — sidecar adapter: minimal route, no new service

Use the existing sidecar. Add one bounded internal operation that does:

```text
request
 -> compose through pizza-agent
 -> verify
 -> return validated native-ready recipe + verifier report
```

Response must distinguish:

- provider unavailable;
- generation failed;
- schema invalid;
- verifier rejected;
- native bridge unavailable;
- success.

Never collapse these states into a generic `ok=true`.

Retain the verifier report identity/hash with the recipe used for Preview/Apply so later runtime evidence can point back to the exact validated input.

## 6. CLD-201 — fifth-tab UI: implement as one state machine

Do not build four unrelated screens. Build one AI tab shell with one mode state.

```text
AI_TAB
  mode = CHAT | LAB | CREW | VOICE
```

Required tab behavior:

```text
stock tab selected -> stock Bakehouse title visible
AI tab selected    -> Barro's header visible, Bakehouse hidden
AI tab closed      -> stock title behavior restored
```

Required geometry invariant:

- fifth tab remains inside the stock side rail;
- Barro's header aspect-fits the title strip;
- close button is never covered;
- switching modes does not create duplicate controls;
- switching back to a stock tab restores stock UI state.

Every visible control must call a real sidecar/native action or be intentionally read-only status. Remove controls that exist only in mockups.

## 7. CLD-301 — Preview / Restore / Apply: use one explicit state machine

Use these states:

```text
IDLE
  -> PREVIEWED
  -> APPLIED

PREVIEWED
  -> RESTORED -> IDLE
  -> APPLIED
```

### Preview

1. Require a validated recipe + verifier identity.
2. Deep-capture the current real `PizzaModel` before mutation.
3. Build the candidate real `PizzaModel`.
4. Call `IPizzaCreatorService.LoadPizzaFromModel(candidate)`.
5. On success, retain operation event + recipe identity + `preview.png`.
6. On failure, do not mark PREVIEWED and do not destroy the captured original.

### Restore

1. Require a pre-preview snapshot.
2. Load the captured original through the native service.
3. Verify identity/state is the captured model.
4. Retain `restore.png` and a runtime event.
5. Clear preview state only after successful restoration.

### Apply

1. Require the currently selected validated recipe.
2. Load/commit it through the native path.
3. Retain `apply.png`, event, recipe identity, verifier identity.
4. Do not silently convert Apply into Save; Save is a separate native action.

## 8. CLD-302 — native Save + exact reload comparator

Save must use the native recipe-book path.

After save:

1. record the modeled snapshot that was saved;
2. return to the stock/native recipe-book route;
3. reload the saved recipe through the game;
4. capture the reloaded `PizzaModel`;
5. compare exact modeled semantics.

Required comparator fields:

- recipe name/identity;
- shape;
- ingredient/container count;
- ingredient IDs;
- size values;
- amount/placements as represented by the model;
- positions;
- rotations;
- profit factor.

Write `saved-reload.json` with explicit per-field agreement. `ACT-405` passes only when the modeled comparison is exact under the repository's accepted normalization rules.

## 9. CLD-401 — Chef Voice: shortest real path

Do not start with provider polish. Prove the physical path first:

```text
Windows microphone enumerated
 -> capture starts
 -> non-empty PCM/audio buffer
 -> capture stops
 -> bounded audio to /transcribe
 -> non-empty transcript
 -> transcript becomes compose prompt
 -> validated recipe returned
```

Evidence must include device/capture metadata, non-zero byte/sample count, transcript presence, and resulting prompt identity. Never retain credentials.

A typed prompt in Voice mode does not satisfy the microphone/STT gates.

## 10. Build/loader/runtime order — avoid debugging the wrong layer

Use this order when local Windows runtime work begins:

1. `BLD-101` exact assembly hashes.
2. `BLD-102` exact plugin compile.
3. `BLD-103` prebuilt/provenance agreement.
4. `BLD-104` Windows compiler parity.
5. `RUN-201` BepInEx initializes.
6. `RUN-202` plugin discovered + Awake completes.
7. `UI-301..303` fifth tab/header behavior.
8. `ACT-401..405` native actions.
9. `VOX-501..502` microphone/STT.
10. `VIS-601..604` final live F8 captures/comparison.
11. Stage All + `RequireComplete`.

Do not debug UI geometry while the loader is unproved. Do not debug Save/reload while Preview cannot create a valid native model.

## 11. Canonical evidence names — produce these, do not invent replacements

Retain the contract artifacts exactly where the proof harness expects them:

- `assembly-hashes.json`
- `compile.log`
- `windows-compile.log`
- `BepInEx-LogOutput.log`
- `runtime-events.jsonl`
- `ui-tab.png`
- `ui-header.png`
- `ui-stock-header.png`
- `preview.png`
- `restore.png`
- `apply.png`
- `saved-reload.json`
- `reload.png`
- `voice.png`
- Chat/Lab/Crew/Voice F8 screenshots
- comparison reports
- final retained proof results exposed through `/proof/latest`

Every runtime event should identify: timestamp, operation, recipe/verifier identity when relevant, success/failure, and a bounded failure reason without secrets.

## 12. Hard stop conditions

Stop promotion immediately if any of these occur:

- exact target assembly hash mismatch;
- wrong runtime profile;
- ingredient ID outside the exact catalog;
- unknown size enum;
- synthetic shape geometry used instead of native `DoughPositions`;
- verifier disagreement with the sidecar payload;
- BepInEx/plugin loader exception relevant to the plugin;
- Preview/Restore/Apply claims without native state change evidence;
- Save claim without native recipe-book route;
- Voice claim without real audio capture;
- screenshot from a mock/test renderer substituted for the live game;
- retained PASS gate missing its required evidence.

## 13. What to hand ChatGPT when Creator is ready

Return one compact handoff containing:

- Creator `main` SHA;
- pizza-agent SHA/identity;
- exact runtime profile;
- proof-results location;
- `/proof/latest` summary;
- four F8 screenshot paths + comparison reports;
- Preview/Restore/Apply/Save/reload artifact paths;
- Voice artifact paths;
- any shared schema/API delta;
- any blocked gate with exact reason.

Do not edit Runtime Proof Studio or Workbench to compensate for a Creator-side delta. Document the delta and hand it over.

## 14. Copy/paste continuation prompt for Claude

> Work only on PC3 Pizza Creator. Read `CLAUDE_HANDOFF.md`, `CLAUDE_NEXT_TASKS_PC3_CREATOR.md`, `CLAUDE_ACCESS_MAP_PC3_CREATOR.md`, `contracts/rc1.acceptance.json`, and `docs/CLAUDE_SKIP_AHEAD_RUNTIME_IMPLEMENTATION_PACKET.md`. Treat the skip-ahead packet as the implementation route and the acceptance contract as truth. Finish the first incomplete dependency, execute its tests/evidence, commit a focused change, then continue to the next dependency without re-auditing settled native architecture. Never promote a runtime gate without its retained evidence, never modify Studio/Workbench implementation, and never expose credentials.
