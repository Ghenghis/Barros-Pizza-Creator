# SCOPE: PC3 PIZZA CREATOR ONLY — Native JPEG Exact-Placement Experiment Harness Specification

**Owner:** Claude — PC3 Pizza Creator  
**Runtime profile:** `creator-0.11.272`  
**Purpose:** make E00–E10 scientifically controllable by letting the existing Creator plugin load a verified research fixture with exact native ingredient transforms, without replacing or bypassing the game's renderer/save path.

This is a research-only extension of the existing native bridge. It must not become a second production recipe authority.

## 1. Why this harness is required

The current generated recipe path can intentionally choose positions/rotations. That is useful for normal design, but it is not precise enough for reverse-engineering experiments where only one independent variable may change.

For experiments such as:

```text
same X/Z, rotation 0° vs 90°
same rotation, X=-4.0 vs X=-3.0
same transforms, ingredient list order A/B vs B/A
same X/Z, Y=1.00 vs 1.01
```

we need to provide exact transforms directly to the existing `PizzaModel` bridge.

## 2. Architecture — reuse the existing native seam

Do not add another renderer, save mechanism, or fake pizza scene.

The research route should be:

```text
research fixture JSON
  -> strict research-fixture validator
  -> existing GameBridge/native model builder
  -> exact PizzaModel / IngredientContainerModel
  -> IPizzaCreatorService.LoadPizzaFromModel(PizzaModel)
  -> stock 3D renderer
  -> stock native recipe save/image-generation path
  -> retained model signature + JPEG
```

The fixture controls **input transforms only**. Everything after `LoadPizzaFromModel` stays native.

## 3. Fixture schema

Suggested canonical file:

```text
research/jpeg-pipeline/fixtures/<experiment>/<variant>.json
```

Shape:

```json
{
  "schema_version": "1.0",
  "experiment_id": "E09",
  "variant": "A",
  "runtime_profile": "creator-0.11.272",
  "name": "JPEG_E09_A",
  "shape": "Round",
  "profit_factor": 0.6,
  "placements": [
    {
      "sequence": 0,
      "ingredient_id": "Bacon",
      "size": "Medium",
      "position": {"x": -3.0, "y": 1.00, "z": 0.0},
      "rotation": {"x": 0.0, "y": 0.0, "z": 0.0}
    }
  ]
}
```

Keep this intentionally small. Do not add AI prose, scores, cost estimates, or fields unrelated to the experiment.

## 4. Strict fixture validation

Reject before touching the live pizza if any condition fails.

### Runtime identity

Require:

```text
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

Resolve dough through the native database service exactly as production does.

### Ingredient identity

Every `ingredient_id` must resolve through the exact installed Creator database for the requested size.

No aliases are repaired inside this harness.

### Size

Require exactly:

```text
Large
Medium
Small
```

and bind to the real enum/model.

### Numeric values

Reject NaN, Infinity, null, and non-numeric values.

### Coordinates

Initial conservative envelope based on observed native placement:

```text
X [-5.5, -0.5]
Z [-2.5, 2.5]
```

Y experiments may intentionally vary around the native layering band. Keep a bounded research envelope, e.g. initially:

```text
Y [0.90, 1.50]
```

until runtime evidence justifies a broader range.

### Rotation

Accept finite degrees. Normalize for comparison/reporting but do not silently change the supplied transform before native model construction unless the game itself normalizes it.

### Sequence/order

`sequence` must be unique and contiguous starting at zero.

Preserve fixture sequence when adding `IngredientContainerModel` objects. This is necessary for E05/E09 ordering experiments.

### Placement count

Use a conservative maximum such as 180, matching the current generator's global cap, unless exact native evidence supports a different research bound.

## 5. Native model construction

Use the same real model classes already used by `GameBridge`.

Conceptually:

```text
model = new PizzaModel()
model.Bind()
model.ID = fixture.name
model.ProfitFactor = fixture.profit_factor
model.doughPositions = database.GetPizzaShape(fixture.shape).DoughPositions

for placement in placements ordered by sequence:
    ingredient = database.GetIngredientByID(placement.ingredient_id, placement.size)
    container = new PizzaModel.IngredientContainerModel()
    container.Bind()
    container.Ingredient = ingredient
    container.Position = exact supplied Vector3
    container.Rotation = exact supplied Vector3
    model.ingredients.Add(container)

model.CalculateCosts()
```

Then use the existing public native load route:

```text
pizzaCreator.LoadPizzaFromModel(model)
```

Do not call a parallel hand-written renderer.

## 6. Required model signature before Save

Immediately after native load settles, capture a signature containing at least:

```text
fixture SHA-256
experiment ID / variant
Creator repo SHA
runtime profile
model ID
profit factor
shape / dough-position identity
ordered placements:
  sequence
  ingredient ID
  numeric enum size
  exact position x/y/z
  exact rotation x/y/z
native calculated cost/price where observable
```

Write it to:

```text
<evidence-run>/<experiment>/<variant>/model-signature.json
```

The JPEG analysis must reference this signature.

## 7. Operator control surface

Prefer a research-only control that does not clutter the normal user UI.

Good options in order:

1. guarded keyboard shortcut opens a research fixture file picker;
2. hidden/advanced section in the AI tab enabled by a research config flag;
3. local sidecar research endpoint bound to loopback, with plugin-side strict validation.

Do not expose arbitrary file execution, assembly loading, or unrestricted paths.

Recommended config:

```text
[Research]
EnableNativeJpegHarness=false
```

Default must be false for normal users/releases.

## 8. Suggested keyboard workflow

When research mode is enabled only:

```text
F6 = choose/load exact research fixture
F7 = write current exact model signature
F8 = existing AI-mode UI screenshot (unchanged)
F9 = existing saved-reload exact model verification (unchanged)
```

Do not reassign F8/F9 because they are already evidence contracts.

The exact key may be changed if conflicts are found; the invariant is that the existing proof hotkeys remain stable.

## 9. Native Save/Image rule

The harness must **not** create the JPEG itself.

After fixture load:

1. use the same native Save/recipe-book path a normal pizza uses;
2. locate/retain the native produced image;
3. bind that image to the fixture/model signature;
4. analyze it with `scripts/analyze_jpeg_experiment.py`.

This preserves the very pipeline we are trying to discover.

## 10. Experiment-specific fixture generation

Create fixtures mechanically so variants cannot accidentally change multiple fields.

### E01 rotation sweep

Base placement remains identical; generated variants change only:

```text
rotation.y
```

### E02 X sweep

Change only:

```text
position.x
```

### E03 Z sweep

Change only:

```text
position.z
```

### E04 Y sweep

Change only:

```text
position.y
```

### E05 overlap/order

Use exactly two placements and construct variants by changing only sequence and/or specified Y.

### E07 size

Same ID/position/rotation; change only size. The native ingredient model may then change mesh/amount/appearance as part of the observation.

### E09 A/B/C/D

Generate B/C/D from canonical A using a script and record a machine diff proving the intended variable is the only changed field family.

## 11. Fixture-diff proof

Before running an A/B experiment, write a comparison artifact:

```json
{
  "experiment_id": "E09",
  "a_sha256": "...",
  "b_sha256": "...",
  "allowed_changed_fields": ["placements[*].rotation.y"],
  "observed_changed_fields": ["placements[0].rotation.y", "placements[1].rotation.y"],
  "unexpected_changes": []
}
```

If `unexpected_changes` is non-empty, do not run/adjudicate that pair as a one-variable experiment.

## 12. Evidence event names

Add research-specific events without pretending they are RC1 production gates:

```text
research.fixture.validated
research.fixture.loaded
research.model.signature_written
research.native_save.requested
research.native_image.discovered
research.native_image.bound_to_model
research.fixture.failed
```

These events support the JPEG research contract only unless a main RC1 gate independently uses the same native action and satisfies its own evidence requirements.

## 13. Fail-closed behavior

On any validator/native-load exception:

- retain failure event and fixture SHA/path identity;
- do not partially apply remaining placements;
- restore the pre-experiment PizzaModel if a modification started;
- do not save a JPEG from a failed fixture;
- do not mark the research variant PASS.

## 14. Completion condition for the harness

The harness is ready when a deterministic test fixture can be loaded twice and the plugin proves:

```text
fixture SHA identical
model signature identical
placement order identical
all ID/size/position/rotation values identical
native reload works
```

JPEG byte identity is **not** required for harness readiness; JPEG determinism is a separate research question.

## 15. Implementation touchpoints for Claude

Keep the change set focused around existing Creator code:

- `plugin-src/Models.cs` — research fixture DTOs only if sharing DTO infrastructure is clean.
- `plugin-src/GameBridge.cs` — exact model construction/reuse of native load and signature logic.
- `plugin-src/BarrosAiPlugin.cs` or `PanelRenderer.cs` — guarded research control/hotkey.
- `plugin-src/EvidenceRecorder.cs` — existing event/screenshot system; add no competing evidence root.
- tests — validator + exact transform/order preservation.

Do not modify Studio or Workbench to implement this Creator harness.
