# SCOPE: PC3 PIZZA CREATOR ONLY — Native JPEG Exact-Model Experiment Harness Specification

**Owner:** Claude — PC3 Pizza Creator  
**Runtime profile:** `creator-0.11.272`  
**Independent stimulus/observation owner:** ChatGPT-owned Runtime Proof Studio  
**Purpose:** execute exact Studio-generated E00–E10 models through the real Creator native load/save/reload route and emit an exact execution receipt that Studio can independently bind to stock output.

This is a research-only extension of the existing Creator native bridge. It must not become a second production recipe authority, stimulus schema, corpus generator, observer, campaign ledger, renderer, or JPEG writer.

## 1. Two shared interoperability contracts

Controlled input:

```text
contracts/creator-controlled-stimulus.schema.json
```

Creator execution receipt:

```text
contracts/creator-controlled-execution-evidence.schema.json
```

Both files exist in Creator and Runtime Proof Studio and must remain semantically identical across the interoperability boundary.

Canonical E00–E10 stimuli are produced only by Studio:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/scripts/generate_creator_controlled_stimuli.py
```

Studio seals the exact stimulus/corpus hashes and independently observes stock output. Claude consumes Studio stimuli read-only and implements only the Creator exact-model executor.

## 2. Why the exact-model executor is required

Normal Creator/Barro's design logic intentionally chooses placement. Controlled reverse-engineering needs exact transforms where one variable can change independently.

Examples:

```text
same model, rotation 0° vs 90°
same rotation/Z/Y, X=-4.0 vs X=-3.0
same transforms, placement array A/B vs B/A
same X/Z/rotation, Y=1.00 vs 1.01
```

The shared stimulus already contains every explicit transform. Never invoke the Barro's golden-angle/distribution placement generator for these cases.

## 3. Canonical stimulus shape

Conceptually:

```json
{
  "schema_version": "1.0",
  "experiment_id": "E09",
  "case_id": "b-rotation-only",
  "runtime_profile": "creator-0.11.272",
  "model": {
    "name": "JPEG-E09-CONTROLLED",
    "shape": "Round",
    "profit_factor": 1.0,
    "placements": [
      {
        "ingredient_id": "Bacon",
        "size": "Medium",
        "position": {"x": -3.75, "y": 1.0, "z": -0.65},
        "rotation": {"x": 0.0, "y": 105.0, "z": 0.0}
      }
    ]
  },
  "operation": {
    "preview_exact_model": true,
    "native_recipe_save": true,
    "reload_verify": false,
    "native_resave_after_reload": false
  },
  "notes": "evidence label only"
}
```

Rules:

- use `case_id`, not a second `variant` dialect;
- placement **array order is the native/serialized order**;
- there is no competing `sequence` field;
- E00 may contain zero placements;
- `operation` is authoritative for Preview/Save/reload/re-save behavior.

## 4. Strict stimulus validation

Reject before modifying the live pizza if any required condition fails.

Require:

```text
schema_version == 1.0
runtime_profile == creator-0.11.272
shape in Round/Square/Star/Triangle
placement count <= 180
all vectors finite numeric values
size in Large/Medium/Small
all ingredient IDs resolve exactly in the installed database
```

Resolve dough positions through:

```text
IDatabaseService.GetPizzaShape(shape).DoughPositions
```

Do not repair aliases in the research executor. Preserve `model.placements` array order exactly; never sort by ID, size, coordinates, or hash.

A bounded research safety envelope may reject obviously unsafe coordinates before native load. That envelope is a safety control, not evidence about stock placement behavior.

## 5. Native model construction

Reuse the real existing model/service seam:

```text
PizzaModel
IngredientContainerModel
IDatabaseService
IPizzaCreatorService.LoadPizzaFromModel
```

Conceptually:

```text
model = new PizzaModel()
model.Bind()
model.ID = stimulus.model.name
model.ProfitFactor = stimulus.model.profit_factor
model.doughPositions += database.GetPizzaShape(stimulus.model.shape).DoughPositions

for placement in stimulus.model.placements IN ARRAY ORDER:
    size = exact IngredientSize mapping
    ingredient = database.GetIngredientByID(placement.ingredient_id, size)
    container = new PizzaModel.IngredientContainerModel()
    container.Bind()
    container.Ingredient = ingredient
    container.Position = exact supplied Vector3
    container.Rotation = exact supplied Vector3
    model.ingredients.Add(container)

model.CalculateCosts()
pizzaCreator.LoadPizzaFromModel(model)
```

No custom renderer or fake pizza scene is allowed.

## 6. Native operation contract

Interpret every stimulus operation literally.

### `preview_exact_model`

If true:

1. capture the pre-experiment restore point;
2. load the exact model through `LoadPizzaFromModel`;
3. after native load settles, inspect/capture the actual live model state used by the execution receipt.

### `native_recipe_save`

If true, invoke only:

```text
IPizzaCreatorService.SaveCurrentPizzaToRecipes()
```

Do not call `EncodeToJPG`, `ScreenCapture`, `ReadPixels`, a custom camera capture, or any substitute image writer to satisfy this operation.

### `reload_verify`

If true:

1. reload through the stock/native recipe-book route;
2. capture the actual reloaded model;
3. require exact stimulus agreement for name/ID, profit factor, shape/dough identity, placement array order, ingredient IDs/sizes, positions, and rotations.

### `native_resave_after_reload`

If true, require successful exact reload verification first, then invoke the same native Save route without modifying the model.

E10 depends on this sequence.

## 7. Required execution-evidence receipt

For **every attempted canonical case**, emit one JSON receipt conforming exactly to:

```text
contracts/creator-controlled-execution-evidence.schema.json
```

Required identity includes:

```text
schema_version = 1.0
kind = pc3-creator-controlled-stimulus-execution-evidence
runtime_profile = creator-0.11.272
experiment_id
case_id
exact stimulus SHA-256
Creator Git repo SHA
exact Assembly-CSharp SHA-256
```

`observed_model` must reflect the actual model after native load, not merely echo the input JSON. Retain:

```text
name
shape
profit_factor
optional native dough-position hash
placements IN ACTUAL ARRAY ORDER:
  index
  ingredient_id
  size
  size_value where available (Large=0, Medium=1, Small=2)
  exact position x/y/z
  exact rotation x/y/z
```

`native_actions` must contain all four actions with:

```text
requested
attempted
success
timestamp_utc
detail
```

If reload verification was requested, `reloaded_model` is required and must describe the actual model obtained through the stock reload path.

Do not set requested actions to success from source presence or expectation. Record observed results only.

## 8. Studio independently verifies the receipt

Studio verifies the receipt with:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/scripts/verify_creator_controlled_execution.py
```

Studio independently compares:

```text
stimulus SHA
experiment/case
exact Creator Assembly-CSharp identity
model name/shape/profit
placement count + ARRAY ORDER
placement index/ID/size/size_value
position and rotation values
requested/attempted/success native-action receipts
reloaded model when requested
```

The receipt path must be supplied to/selected by Studio's canonical observer.

A missing or mismatching receipt returns the canonical campaign below `fully_bound` and uses exit code `5` in the Studio wrapper.

The receipt does not prove the stock JPEG exists. Studio independently observes UserData before/after and binds the actual changed/created stock JPEG.

## 9. Three-link proof chain

The intended separation is:

```text
Studio sealed stimulus
    -> Claude Creator exact-model executor
    -> Creator execution-evidence receipt
    -> Studio independent stimulus/model/action/assembly verification
    -> native Creator Save/reload/re-save
    -> untouched stock Creator UserData/JPEG
    -> Studio independent before/after/output analysis
    -> independent Studio/Creator JPEG parser agreement
```

Claude owns the native executor/receipt producer. Studio owns stimulus generation/sealing, independent receipt verification, stock-output observation, parser cross-validation, campaign ledger, and JRE input-readiness board.

Neither side may manufacture the other's evidence.

## 10. Campaign states relevant to Claude

Studio's campaign can report:

```text
not_run
observed
cross_validated
fully_bound
unresolved
mismatch
```

`cross_validated` is **not** enough for controlled JRE input readiness: stock output/parser evidence exists but the exact Creator execution binding is absent/not PASS.

`fully_bound` means:

```text
exact sealed stimulus
+
Studio-verified exact Creator execution receipt/model/actions/assembly
+
stock output observation
+
independent JPEG parser agreement
```

`fully_bound` is the strongest controlled-evidence state, but it still does not prove the native save/render/JPEG implementation call chain.

## 11. One-variable experiment proof

Before interpreting an A/B pair, compare the shared stimuli with:

```text
scripts/compare_controlled_stimuli.py
```

`case_id` and `notes` are evidence labels. Substantive model/operation changes must match the intended variable family only.

Example E01 allowance:

```text
--allow "model.placements[*].rotation.y"
```

Studio's generator is regression-tested to keep model names constant inside one-variable sweeps unless name itself is the variable.

## 12. Research-only operator surface

Prefer a guarded research path that does not clutter normal Creator use.

Recommended default:

```text
[Research]
EnableNativeJpegHarness=false
```

Possible controls:

```text
F6 = select/load canonical controlled stimulus
F7 = write/retain current execution receipt/model evidence
F8 = existing AI-mode screenshot evidence (unchanged)
F9 = existing native saved-reload verification (unchanged)
```

Do not reassign F8/F9.

A bounded loopback research endpoint is acceptable if it accepts only the shared stimulus contract and cannot execute arbitrary files/paths.

## 13. Canonical experiments

Studio generates 60 E00–E10 cases.

- **E00:** identical dough-only repeats.
- **E01:** Y rotation only.
- **E02:** X only.
- **E03:** Z only.
- **E04:** Y only.
- **E05:** distinguishable ingredient overlap/order/Y relationships.
- **E06:** piece count using a fixed explicit transform prefix; not a stock-placement claim.
- **E07:** size only.
- **E08:** shape only; explicit placement transform fixed while Creator resolves native dough positions.
- **E09:** A baseline, B rotation-only, C position-only, D array-order-only; model name fixed.
- **E10:** native save -> stock reload -> exact model verification -> native re-save.

Use Studio's `RUN_NEXT_CREATOR_JPEG_CASE.bat`/campaign ledger; do not hand-maintain a competing corpus or silently skip unresolved current cases.

## 14. Evidence events

Use the existing Creator `EvidenceRecorder`; do not create a competing evidence root.

Recommended events:

```text
research.stimulus.validated
research.stimulus.rejected
research.stimulus.loaded
research.model.signature_written
research.execution.receipt_written
research.native_save.requested
research.native_save.returned
research.native_reload.verified
research.native_reload.failed
research.native_resave.requested
research.stimulus.failed
```

Do not emit Studio-owned native-image discovery/parser/campaign claims as if Creator proved them.

## 15. Fail-closed behavior

On validation/native-load failure:

- retain experiment ID, case ID, stimulus hash, error, profile and Creator identity;
- do not partially apply remaining placements;
- restore the pre-experiment model if live modification began;
- do not request native save from an invalid model;
- emit a truthful failed execution receipt/event where the shared schema permits the observed state;
- do not promote any JRE gate.

If native Save returns but Studio cannot find/bind stock output, leave the case unresolved rather than generating a replacement JPEG.

## 16. Harness readiness

The executor is ready when the same canonical stimulus can be applied twice and Creator can emit receipts that Studio independently verifies for:

```text
same stimulus SHA
same exact Creator assembly identity
same observed model
same placement array order
same IDs/sizes/positions/rotations
correct native-action receipts
successful native load
```

For E10-capable readiness also require exact native reload-model verification.

JPEG byte identity is not required for executor readiness; JPEG determinism is a separate JRE question.

## 17. Claude implementation touchpoints

Keep the change focused around existing Creator code:

- `plugin-src/Models.cs` — shared stimulus/execution-evidence DTOs only if useful; mirror the contracts exactly.
- `plugin-src/GameBridge.cs` — exact model construction/load/save/reload and actual model inspection.
- `plugin-src/BarrosAiPlugin.cs` and/or `PanelRenderer.cs` — guarded research controls only.
- `plugin-src/EvidenceRecorder.cs` — execution receipt/event retention in the existing evidence system.
- tests — shared stimulus validation, exact transform/order preservation, E00 empty model, operation gating, receipt schema/identity, reload receipt.

Do not modify Runtime Proof Studio or Barro's Workbench from the Creator workstream. If either shared schema needs a change, document/coordinate the interoperability delta instead of silently diverging Creator's copy.
