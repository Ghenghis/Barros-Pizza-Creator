# SCOPE: PC3 PIZZA CREATOR ONLY — Native Pizza JPEG Algorithm Notebook

**Owner:** Claude  
**Target:** Pizza Creator `creator-0.11.272`  
**Independent stimulus producer/observer:** ChatGPT-owned Runtime Proof Studio  
**Status:** **PARTIALLY CHARACTERIZED — DO NOT CALL COMPLETE**

This is the final evidence notebook for the stock/native pizza-image pipeline. Unknowns are intentionally explicit. Do not replace `UNKNOWN` with an inference unless the classification and retained evidence are recorded.

## 1. Truth classification

Every finding uses exactly one classification:

- `PROVEN_FROM_SOURCE` — exact supplied/decompiled Creator source establishes the behavior/path.
- `PROVEN_FROM_RUNTIME` — exact Creator 0.11.272 live trace/call stack/argument/render evidence establishes it.
- `INFERRED_AND_VALIDATED` — controlled experiments mathematically support it, but direct source/runtime identity is not yet available.
- `UNKNOWN` — unresolved.

## 2. Exact target identity

| Fact | Classification | Value/evidence |
|---|---|---|
| Creator runtime profile | PROVEN_FROM_SOURCE | `creator-0.11.272` contracts/handoff |
| Unity version | PROVEN_FROM_SOURCE | `2017.3.1p4 x64` |
| Assembly-CSharp SHA-256 | PROVEN_FROM_SOURCE | `ebf8698df7cb4af904c98c299994705ea529efbdf1e8ccb3e7ca8cb42a1cbc1c` |
| Assembly-CSharp-firstpass SHA-256 | PROVEN_FROM_SOURCE | `f9cbf0951fc4d4b0788c47bbe41a3820fa333d293175bbb7cb398eb4728fd284` |
| shared controlled stimulus schema | PROVEN_FROM_SOURCE | `contracts/creator-controlled-stimulus.schema.json`; Creator and Studio copies must remain semantically identical |

## 3. Input pizza model facts

| Component | Classification | Current evidence |
|---|---|---|
| model ID/name serialized | PROVEN_FROM_SOURCE | `PizzaModel.ID` / save model keys |
| profit factor serialized | PROVEN_FROM_SOURCE | `PizzaModel.ProfitFactor` |
| dough positions serialized | PROVEN_FROM_SOURCE | `DoughPositions` |
| ingredient ID serialized | PROVEN_FROM_SOURCE | `Ingredient` / `IngredientID` |
| ingredient size serialized | PROVEN_FROM_SOURCE | `Size`; `Large=0`, `Medium=1`, `Small=2` |
| ingredient position serialized | PROVEN_FROM_SOURCE | `Position` |
| ingredient rotation serialized | PROVEN_FROM_SOURCE | `Rotation` |
| placement array/order preserved in model | PROVEN_FROM_SOURCE | ordered `PizzaModel.ingredients`; image effect still UNKNOWN |
| four shapes | PROVEN_FROM_SOURCE | Round/Square/Star/Triangle |
| native model load drives real 3D pizza | PROVEN_FROM_SOURCE | `IPizzaCreatorService.LoadPizzaFromModel(PizzaModel)` path |

## 4. Save trigger and call graph

| Question | Classification | Finding/evidence |
|---|---|---|
| native recipe save entry | PROVEN_FROM_SOURCE | `SaveCurrentPizzaToRecipes()` exists and is used by current bridge |
| exact method that initiates image generation | UNKNOWN | run static tracer + ILSpy |
| image generation synchronous with recipe save? | UNKNOWN | source/runtime trace required |
| image generation via event subscriber? | UNKNOWN | source/runtime trace required |
| recipe-card/thumbnail refresh involved? | UNKNOWN | source/runtime trace required |
| exact call graph save -> render -> encode -> write | UNKNOWN | JRE-001/JRE-002 |

Static discovery artifacts:

```text
research/jpeg-pipeline/static-trace/trace.json
research/jpeg-pipeline/static-trace/candidate-methods.csv
research/jpeg-pipeline/static-trace/hits.csv
research/jpeg-pipeline/static-trace/probable-call-references.csv
```

Status: `UNKNOWN` until run and adjudicated in ILSpy/dnSpyEx.

Runtime trace references:

```text
UNKNOWN
```

## 5. Controlled stimulus / observation architecture

The reverse-engineering experiments intentionally use two independent workstreams:

```text
Studio canonical generator
  -> shared controlled stimulus
  -> Claude Creator exact-model executor
  -> native LoadPizzaFromModel
  -> stock native Save / reload / re-save
  -> stock Creator UserData/JPEG
  -> Studio controlled observer
  -> quantitative/JPEG analysis
```

### Canonical producer

Studio-owned:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/scripts/generate_creator_controlled_stimuli.py
```

The canonical corpus contains 60 cases covering E00–E10.

### Creator executor

Claude-owned implementation contract:

```text
docs/NATIVE_JPEG_EXPERIMENT_HARNESS_SPEC.md
```

The executor binds exact shared-stimulus transforms directly to real `PizzaModel` objects. It must not run the normal Barro's/golden-angle placement algorithm for controlled fixtures and must not generate/encode/rewrite the native JPEG.

### Independent observer

Studio-owned launcher:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/CAPTURE_CREATOR_CONTROLLED_JPEG_EXPERIMENT.bat
```

The observer is responsible for independently retaining/binding stock UserData/JPEG outputs and comparison evidence. Creator should not manufacture Studio's observer result.

### One-variable input validator

Creator utility:

```text
scripts/compare_controlled_stimuli.py
```

This distinguishes evidence-label fields (`case_id`, `notes`) from substantive model/operation changes and can fail closed on unexpected changed field families.

## 6. Render scene / pizza object reconstruction

| Question | Classification | Finding/evidence |
|---|---|---|
| saved image uses current live pizza scene | UNKNOWN | experiment/source trace |
| saved image reconstructs hidden pizza from PizzaModel | UNKNOWN | source/runtime trace |
| exact dough mesh/prefab used | UNKNOWN | AssetRipper/runtime |
| exact ingredient mesh/material mapping | UNKNOWN | AssetRipper/runtime |
| ingredient array order affects object creation | PROVEN_FROM_SOURCE for model load; image effect UNKNOWN | E05/E09 required |
| Y depth affects visible stacking | UNKNOWN | E04/E05 + RenderDoc/source |
| material render queues/depth tests | UNKNOWN | RenderDoc/source |

## 7. Camera

| Parameter | Classification | Value/evidence |
|---|---|---|
| camera object/class | UNKNOWN | JRE-003 |
| dedicated image camera? | UNKNOWN | source/AssetRipper/runtime |
| perspective vs orthographic | UNKNOWN | source + `fit_jpeg_camera_mapping.py` |
| position | UNKNOWN | runtime/source |
| rotation | UNKNOWN | runtime/source |
| FOV / orthographic size | UNKNOWN | runtime/source |
| near/far clip | UNKNOWN | runtime/source |
| culling mask | UNKNOWN | runtime/source |
| clear flags/background | UNKNOWN | runtime/source |
| world X/Z -> JPEG u/v | UNKNOWN | E02/E03 affine/homography evidence |

Camera-calibration evidence:

```text
UNKNOWN — collect label,x,z,u,v from canonical E02/E03 outputs and run scripts/fit_jpeg_camera_mapping.py
```

The affine/homography result is `INFERRED_AND_VALIDATED` at best until source/runtime identifies the actual Camera path.

## 8. Render target and readback

| Question | Classification | Finding/evidence |
|---|---|---|
| RenderTexture used | UNKNOWN | source/runtime/RenderDoc |
| render target width/height | UNKNOWN | JRE-003/004 |
| target format | UNKNOWN | runtime/RenderDoc |
| MSAA | UNKNOWN | runtime/RenderDoc |
| `Camera.Render()` used | UNKNOWN | source/runtime |
| `Texture2D.ReadPixels()` used | UNKNOWN | source/runtime |
| `Graphics.Blit()` used | UNKNOWN | source/runtime |
| readback texture format | UNKNOWN | runtime/source |

## 9. Crop / resize / orientation / colorspace

| Component | Classification | Finding/evidence |
|---|---|---|
| source render dimensions | UNKNOWN | JRE-004 |
| crop rectangle | UNKNOWN | source/runtime + camera mapping |
| output JPEG dimensions | UNKNOWN | native samples |
| resize/downsample algorithm | UNKNOWN | source + controlled geometry |
| vertical flip | UNKNOWN | camera mapping/source |
| alpha flattening/background | UNKNOWN | source/runtime |
| linear/gamma/sRGB conversion | UNKNOWN | source/runtime/RenderDoc |
| post-processing | UNKNOWN | source/RenderDoc |

## 10. Ingredient transform -> image transform

| Component | Classification | Finding/evidence |
|---|---|---|
| X effect on image u | UNKNOWN | canonical E02 |
| Z effect on image v | UNKNOWN | canonical E03 |
| cross-axis coupling | UNKNOWN | affine/homography fit |
| native Y yaw -> image orientation | UNKNOWN | canonical E01 + `fit_jpeg_orientation_transfer.py` |
| Large/Medium/Small visible footprint | UNKNOWN | canonical E07 |
| ingredient-specific mesh footprint | UNKNOWN | AssetRipper + E07 |
| Y layer -> occlusion | UNKNOWN | canonical E04/E05 |
| array order -> occlusion | UNKNOWN | canonical E05/E09 |

## 11. JPEG encoder

Official Unity 2017.3 research boundary:

- `ScreenCapture.CaptureScreenshot` writes PNG, so it cannot by itself explain a final stock JPEG.
- `ImageConversion.EncodeToJPG` is a candidate API and supports quality 1–100; default quality is documented as 75 when omitted.

These are candidate clues, not claims that PC3 uses them.

| Encoder component | Classification | Finding/evidence |
|---|---|---|
| final JPEG API/library | UNKNOWN | JRE-002/005 |
| explicit quality argument | UNKNOWN | source/runtime |
| DQT fingerprint | UNKNOWN | native sample + `fingerprint_jpeg_encoder.py` |
| standard IJG quality-family match | UNKNOWN | native sample |
| DHT fingerprint | UNKNOWN | native sample |
| component sampling | UNKNOWN | native sample |
| baseline/progressive | UNKNOWN | native sample |
| restart interval | UNKNOWN | native sample |
| APP/COM metadata | UNKNOWN | native sample |
| encoder configuration stable across pizzas | UNKNOWN | multi-image corpus |

Forensics procedure:

```text
scripts/analyze_jpeg_experiment.py
scripts/fingerprint_jpeg_encoder.py
docs/JPEG_ENCODER_FORENSICS_GUIDE.md
```

A matching IJG quantization quality is a structural fingerprint, not proof of encoder implementation.

## 12. Determinism

| Experiment | Classification | Result/evidence |
|---|---|---|
| identical model repeated native saves | UNKNOWN | canonical E00 / JRE-006 |
| same model after native reload -> same model signature | main RC1 mechanism exists; live result UNKNOWN | F9 / E10 / ACT-405 |
| same model after native reload -> same JPEG bytes | UNKNOWN | canonical E10 / JRE-012 |
| same model -> same decoded pixels | UNKNOWN | E00/E10 |
| same model -> same encoder fingerprint | UNKNOWN | E00/E10 |
| frame timing affects pixels | UNKNOWN | repeated saves/runtime trace |
| metadata/timestamps affect bytes | UNKNOWN | repeated saves/JPEG marker diff |

## 13. Controlled A/B/C/D experiment — E09

Canonical Studio E09 uses one fixed model name and the same four valid ingredients.

- **A `a-baseline`:** exact baseline IDs/counts/sizes/positions/rotations/order.
- **B `b-rotation-only`:** same IDs/counts/sizes/positions/order; rotations only changed.
- **C `c-position-only`:** same IDs/counts/sizes/rotations/order; positions only changed.
- **D `d-order-only`:** exact baseline transforms; placement array order reversed.

Before runtime interpretation, use `scripts/compare_controlled_stimuli.py` to prove the intended substantive field family is the only change.

Inputs are produced by Studio's canonical generator; there is **no Creator-side E09 generator or local fixture authority**.

Results:

```text
A: UNKNOWN
B: UNKNOWN
C: UNKNOWN
D: UNKNOWN
A vs B pixel/encoder analysis: UNKNOWN
A vs C pixel/encoder analysis: UNKNOWN
A vs D pixel/encoder analysis: UNKNOWN
```

Do not fill until stock native JPEGs and exact model-signature evidence exist and Studio has independently bound the outputs to the correct cases.

## 14. Current Barro's placement algorithm — separate from stock native behavior

Classification: `PROVEN_FROM_SOURCE` for the Barro's plugin implementation, **not** the stock manual/native placement algorithm.

Reference:

```text
docs/CURRENT_PIZZA_PLACEMENT_ALGORITHM_REFERENCE.md
```

Current core behavior:

```text
deterministic seed
+ golden-angle angular sequence
+ distribution-specific radius
+ seeded Y rotation
+ global Y layer increment 0.01
+ native PizzaModel
+ native LoadPizzaFromModel renderer
```

Stock Creator placement algorithm:

```text
UNKNOWN / not equivalent merely because the renderer accepts the same transforms
```

Controlled JPEG stimuli deliberately bypass the Barro's placement generator so its algorithm cannot confound stock render/save measurements.

## 15. Research-backed enhanced algorithm candidate

This is not stock behavior and is not default until characterized/tested.

Candidate:

```text
exact native dough domain
-> deterministic golden-angle/candidate initialization
-> variable/anisotropic Poisson separation
-> sample elimination to exact piece count
-> bounded capacity/Lloyd-style density relaxation
-> ingredient-aware deterministic orientation
-> measured native-compatible depth/layer ordering
-> explicit verified transforms
-> native PizzaModel
-> native renderer
-> native image generator when possible
```

Research basis:

```text
docs/RESEARCH_BACKED_PLACEMENT_AND_JPEG_GUIDE.md
```

## 16. Native reuse / improvement decision

Do not decide until JRE-001..012 are resolved.

| Option | State | Decision evidence |
|---|---|---|
| exact native image generator reuse | UNKNOWN | characterize call path first |
| native renderer + controlled deterministic capture | UNKNOWN | evaluate if native image save is nondeterministic/limited |
| independent renderer/encoder replica | LAST RESORT / NOT SELECTED | only if native reuse/capture is impossible |
| enhanced deterministic placement | OPTIONAL CANDIDATE | compare after native behavior characterized |

Final required decision classification:

```text
JRE-014: NOT_RUN
```

## 17. Completion checklist

The notebook may change status to `CHARACTERIZED` only after all required gates in:

```text
contracts/jpeg-reverse-engineering.acceptance.json
```

are PASS with retained evidence.

Required final source set includes:

```text
static source trace
live save/render/JPEG trace
Studio-bound controlled experiment corpus results
camera mapping
orientation mapping
overlap/order analysis
size/shape analysis
native save/reload determinism
JPEG encoder fingerprint and implementation proof
native-reuse/improvement decision
```

Until then this heading must remain:

**PARTIALLY CHARACTERIZED — DO NOT CALL COMPLETE**
