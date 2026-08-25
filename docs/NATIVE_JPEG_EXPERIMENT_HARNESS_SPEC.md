# SCOPE: PC3 PIZZA CREATOR ONLY — Native JPEG Exact-Model Experiment Harness Specification

**Owner:** Claude — PC3 Pizza Creator  
**Runtime profile:** `creator-0.11.272`  
**Shared stimulus producer/observer:** ChatGPT-owned Runtime Proof Studio  
**Purpose:** make E00–E10 scientifically controllable by letting the existing Creator plugin load exact native model transforms from the shared Creator↔Studio stimulus contract, without replacing or bypassing the game's renderer/save path.

This is a research-only extension of the existing Creator native bridge. It must not become a second production recipe authority, a second stimulus schema, or a second JPEG generator.

## 1. One canonical stimulus contract

The only controlled-stimulus schema is:

```text
contracts/creator-controlled-stimulus.schema.json
```

The file exists in both Creator and Runtime Proof Studio and must remain semantically identical.

Canonical E00–E10 stimuli are produced by the **Studio-owned** generator:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/scripts/generate_creator_controlled_stimuli.py
```

Claude may consume its output read-only. Claude must not create or maintain a competing corpus generator in the Creator repository.

The Creator research lab button **Generate Canonical Studio Stimuli** invokes that Studio generator without modifying Studio.

## 2. Why an exact-model executor is still required

Normal Creator recipe generation intentionally chooses positions/rotations. That is useful for design but unsuitable for experiments where only one independent variable may change.

Examples:

```text
same X/Z/size/model name, rotation 0° vs 90°
same rotation/Z/Y/model name, X=-4.0 vs X=-3.0
same transforms/model name, placement array A/B vs B/A
same X/Z/rotation/model name, Y=1.00 vs 1.01
```

The Studio stimulus already supplies every transform. The Creator executor must preserve those exact values and must **not** invoke the Barro's golden-angle/distribution placement generator.

## 3. Shared fixture shape

A canonical stimulus looks conceptually like:

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

Important differences from the retired local format:

- use `case_id`, not `variant`;
- model fields live under `model`;
- placement **array order is the serialized/native order**;
- there is **no `sequence` field**;
- E00 may intentionally contain an empty placements array;
- `operation` explicitly controls Preview/Save/reload/re-save behavior.

## 4. Strict runtime validation

Reject the stimulus before modifying the live pizza if any required condition fails.

### Identity

Require:

```text
schema_version == 1.0
runtime_profile == creator-0.11.272
```

### Shape

Require one of:

```text
Round
Square
Star
Triangle
```

Resolve the real dough positions through:

```text
IDatabaseService.GetPizzaShape(shape).DoughPositions
```

### Ingredients and sizes

Every placement must resolve through the exact installed Creator database using the requested size.

Allowed size names:

```text
Large
Medium
Small
```

Do not repair aliases inside the research executor. An invalid stimulus must fail closed so the experiment remains exact.

### Numeric values

Reject NaN, Infinity, null, and non-numeric vectors.

The shared JSON schema intentionally does not over-constrain research coordinates because controlled experiments may need to probe a boundary. The Creator executor should nevertheless apply a **research safety envelope** before native load and record any rejected out-of-envelope stimulus. Initial conservative values may use observed native ranges, but changing that envelope is a research-safety change, not evidence about the stock algorithm.

### Placement order

Preserve `model.placements` array order exactly when constructing `PizzaModel.ingredients`.

Never sort placements by ID, size, coordinates, or hash. E05/E09 explicitly study order effects.

### Placement count

Reject more than 180 placements because the shared schema caps the corpus at 180. E00 with zero placements is valid.

## 5. Native model construction

Use the same real model classes and services already used by `GameBridge`.

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
```

Then use the existing public native seam:

```text
pizzaCreator.LoadPizzaFromModel(model)
```

No custom rendering occurs in this executor.

## 6. Operation contract

Interpret `operation` literally.

### `preview_exact_model`

If true:

1. capture a pre-experiment restore point;
2. load the exact constructed model through `LoadPizzaFromModel`;
3. retain a model signature after the native load settles.

### `native_recipe_save`

If true, invoke only the stock/native path already exposed by:

```text
IPizzaCreatorService.SaveCurrentPizzaToRecipes()
```

The executor must not call `EncodeToJPG`, `ScreenCapture`, `ReadPixels`, or any substitute image writer to satisfy this operation. The native game must produce whatever recipe image/JPEG it normally produces.

### `reload_verify`

If true:

1. reload through the stock/native recipe-book path;
2. compare the actual reloaded `PizzaModel` to the retained model signature;
3. require exact ID/name, profit factor, dough positions, placement array order, ingredient IDs/sizes, positions, and rotations.

### `native_resave_after_reload`

If true, require a successful native reload verification first, then invoke the same stock save path again without modifying the model.

E10 depends on this exact sequence.

## 7. Required input identity and model signature

For every case retain at least:

```text
experiment_id
case_id
shared stimulus SHA-256
Creator repo SHA
runtime profile
model name
shape / native dough-position identity
profit factor
placements in exact array order:
  index
  ingredient ID
  numeric enum size
  exact position x/y/z
  exact rotation x/y/z
native calculated cost/price where observable
operation flags
timestamps
```

Write/reference it under the run evidence for that experiment/case.

The native JPEG/image must be bound to this exact stimulus/model identity by the Studio observer before it can support JRE analysis.

## 8. One-variable experiment proof

Before treating an A/B pair as a controlled one-variable experiment, compare the two shared stimuli with:

```text
scripts/compare_controlled_stimuli.py
```

The comparator:

- validates the shared contract shape;
- treats `case_id` and `notes` as evidence labels;
- reports substantive model/operation changes separately;
- normalizes placement indexes to `model.placements[*]` families;
- can fail closed with `--allow` patterns.

Example for an E01 pair:

```text
--allow "model.placements[*].rotation.y"
```

A rotation experiment is invalid if the comparator also sees X/Z/size/name/shape/profit/operation changes.

### Important model-name rule

Within a controlled sweep the **model name must remain constant** unless model name itself is the variable under study.

Studio's canonical generator is regression-tested for constant model names within E00–E09 because changing the name could affect recipe lookup, native output filename, metadata, or save behavior and become a hidden confound.

## 9. Research-only operator surface

Prefer a guarded research path that does not clutter the normal Creator UI.

Recommended config:

```text
[Research]
EnableNativeJpegHarness=false
```

Default is false.

Possible operator path:

```text
F6 = select/load canonical controlled stimulus
F7 = write current exact model signature
F8 = existing AI-mode screenshot evidence (unchanged)
F9 = existing saved-reload verification (unchanged)
```

Do not reassign F8/F9.

Alternatively a bounded loopback research endpoint may be used if it accepts only the shared stimulus contract and cannot read arbitrary paths or execute arbitrary files.

## 10. Two-party proof chain

The intended separation is:

```text
Studio canonical generator
    -> explicit controlled stimulus
    -> Claude Creator exact-model executor
    -> native LoadPizzaFromModel
    -> stock native Save / reload / re-save
    -> stock Creator UserData/JPEG
    -> Studio controlled observer
    -> before/after/hash/pixel/DQT/DHT/DCT/transform analysis
```

Claude is the **stimulus executor/native producer**.
Studio is the **independent observer/analyzer**.

Neither side may manufacture the other's evidence.

## 11. Canonical experiments

Studio generates 60 cases covering E00–E10.

Key invariants:

- **E00:** identical dough-only model repeated; only evidence `case_id` differs.
- **E01:** Y rotation only.
- **E02:** X only.
- **E03:** Z only.
- **E04:** Y only.
- **E05:** two distinguishable ingredients; order and/or specified Y relationship.
- **E06:** piece-count study using a fixed prefix of explicit deterministic transforms; this is a controlled stimulus, not a stock-placement claim.
- **E07:** size only.
- **E08:** shape only; placement transform held constant and native dough positions resolved by Creator.
- **E09:** A baseline, B rotation-only, C position-only, D array-order-only; model name fixed.
- **E10:** native save -> stock reload -> exact model verification -> native re-save.

## 12. Evidence event names

Add research-specific events to the existing `EvidenceRecorder`; do not create a competing evidence root.

Recommended events:

```text
research.stimulus.validated
research.stimulus.rejected
research.stimulus.loaded
research.model.signature_written
research.native_save.requested
research.native_save.returned
research.native_reload.verified
research.native_reload.failed
research.native_resave.requested
research.stimulus.failed
```

If native image discovery/binding is performed by Studio rather than Creator, do **not** duplicate Studio's observer event as a Creator claim.

## 13. Fail-closed behavior

On validation/native-load failure:

- retain experiment ID, case ID, stimulus hash, error, and profile;
- do not partially apply remaining placements;
- restore the pre-experiment model if a live modification began;
- do not request native save from an invalid model;
- do not promote a JRE gate.

If a native save call returns but Studio cannot find/bind the expected stock output, record the observation as unresolved/failed rather than generating a replacement JPEG.

## 14. Harness readiness test

The executor is ready when the same canonical stimulus can be applied twice and retained evidence proves:

```text
same stimulus SHA
same model signature
same placement array order
same IDs/sizes/positions/rotations
same native profile
successful native load
```

For an E10-capable harness also require native reload exact-model verification.

JPEG byte identity is **not** a prerequisite for harness readiness; JPEG determinism is itself JRE research.

## 15. Claude implementation touchpoints

Keep the change focused around existing Creator code:

- `plugin-src/Models.cs` — shared stimulus DTOs if useful; mirror the shared contract exactly rather than inventing another DTO dialect.
- `plugin-src/GameBridge.cs` — exact `PizzaModel` construction, load, save, restore/reload signature logic.
- `plugin-src/BarrosAiPlugin.cs` and/or `PanelRenderer.cs` — guarded research control only.
- `plugin-src/EvidenceRecorder.cs` — existing event system.
- tests — shared-stimulus validation, exact transform/order preservation, empty E00 support, operation gating.

Do not modify Runtime Proof Studio or Barro's Workbench from the Creator workstream. If the shared stimulus schema needs a change, document a cross-workstream schema delta and coordinate it rather than silently diverging the Creator copy.
