# SCOPE: PC3 PIZZA CREATOR ONLY — Native Pizza JPEG Algorithm Notebook

**Owner:** Claude  
**Target:** Pizza Creator `creator-0.11.272`  
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
| four shapes | PROVEN_FROM_SOURCE | Round/Square/Star/Triangle |
| native model reload drives real 3D pizza | PROVEN_FROM_SOURCE | `IPizzaCreatorService.LoadPizzaFromModel(PizzaModel)` path |

## 4. Save trigger and call graph

| Question | Classification | Finding/evidence |
|---|---|---|
| native recipe save entry | PROVEN_FROM_SOURCE | `SaveCurrentPizzaToRecipes()` exists and is used by current bridge |
| exact method that initiates image generation | UNKNOWN | run static tracer + ILSpy |
| image generation synchronous with recipe save? | UNKNOWN | source/runtime trace required |
| image generation via event subscriber? | UNKNOWN | source/runtime trace required |
| recipe-card/thumbnail refresh involved? | UNKNOWN | source/runtime trace required |
| exact call graph save -> render -> encode -> write | UNKNOWN | JRE-001/JRE-002 |

### Static evidence references

```text
research/jpeg-pipeline/static-trace/trace.json          UNKNOWN until run
research/jpeg-pipeline/static-trace/candidate-methods.csv
research/jpeg-pipeline/static-trace/probable-call-references.csv
```

### Runtime trace references

```text
UNKNOWN
```

## 5. Render scene / pizza object reconstruction

| Question | Classification | Finding/evidence |
|---|---|---|
| saved image uses current live pizza scene | UNKNOWN | experiment/source trace |
| saved image reconstructs a hidden pizza from PizzaModel | UNKNOWN | source/runtime trace |
| exact dough mesh/prefab used | UNKNOWN | AssetRipper/runtime |
| exact ingredient mesh/material mapping | UNKNOWN | AssetRipper/runtime |
| ingredient list order affects object creation | PROVEN_FROM_SOURCE for current LoadPizzaFromModel model path; image effect UNKNOWN | model preserves ordered placements; E05/E09 required |
| Y depth affects visible stacking | UNKNOWN | E04/E05 + RenderDoc/source |
| material render queues/depth tests | UNKNOWN | RenderDoc/source |

## 6. Camera

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

### Camera-calibration evidence

```text
UNKNOWN — collect label,x,z,u,v and run scripts/fit_jpeg_camera_mapping.py
```

## 7. Render target and readback

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

## 8. Crop / resize / orientation / colorspace

| Component | Classification | Finding/evidence |
|---|---|---|
| source render dimensions | UNKNOWN | JRE-004 |
| crop rectangle | UNKNOWN | source/runtime + camera mapping |
| output JPEG dimensions | UNKNOWN | native samples |
| resize/downsample algorithm | UNKNOWN | source + controlled render geometry |
| vertical flip | UNKNOWN | camera mapping/source |
| alpha flattening/background | UNKNOWN | source/runtime |
| linear/gamma/sRGB conversion | UNKNOWN | source/runtime/RenderDoc |
| post-processing | UNKNOWN | source/RenderDoc |

## 9. Ingredient transform -> image transform

| Component | Classification | Finding/evidence |
|---|---|---|
| X effect on image u | UNKNOWN | E02 |
| Z effect on image v | UNKNOWN | E03 |
| cross-axis coupling | UNKNOWN | affine/homography fit |
| native Y yaw -> image orientation | UNKNOWN | E01 + `fit_jpeg_orientation_transfer.py` |
| Large/Medium/Small visible footprint | UNKNOWN | E07 |
| ingredient-specific mesh footprint | UNKNOWN | AssetRipper + E07 |
| Y layer -> occlusion | UNKNOWN | E04/E05 |
| list order -> occlusion | UNKNOWN | E05/E09 |

## 10. JPEG encoder

Official Unity 2017.3 research boundary:

- `ScreenCapture.CaptureScreenshot` writes PNG, so it cannot by itself explain a final stock JPEG.
- `ImageConversion.EncodeToJPG` is a candidate API and supports quality 1–100; default quality is documented as 75 when omitted.

These are **candidate clues**, not claims that PC3 uses them.

| Encoder component | Classification | Finding/evidence |
|---|---|---|
| final JPEG API/library | UNKNOWN | JRE-002/005 |
| explicit quality argument | UNKNOWN | source/runtime |
| DQT fingerprint | UNKNOWN | native sample + `fingerprint_jpeg_encoder.py` |
| standard IJG quality match | UNKNOWN | native sample |
| DHT fingerprint | UNKNOWN | native sample |
| component sampling | UNKNOWN | native sample |
| baseline/progressive | UNKNOWN | native sample |
| restart interval | UNKNOWN | native sample |
| APP/COM metadata | UNKNOWN | native sample |
| encoder configuration stable across pizzas | UNKNOWN | multi-image corpus |

### Encoder evidence

```text
UNKNOWN — use scripts/fingerprint_jpeg_encoder.py
```

## 11. Determinism

| Experiment | Classification | Result/evidence |
|---|---|---|
| identical model repeated native saves | UNKNOWN | E00/JRE-006 |
| same model after native reload -> same model signature | main RC1 mechanism exists; live result UNKNOWN | F9/ACT-405 |
| same model after native reload -> same JPEG bytes | UNKNOWN | E10/JRE-012 |
| same model -> same decoded pixels | UNKNOWN | E00/E10 |
| same model -> same encoder fingerprint | UNKNOWN | E00/E10 |
| frame timing affects pixels | UNKNOWN | repeated saves/runtime trace |
| metadata/timestamps affect bytes | UNKNOWN | repeated saves/JPEG marker diff |

## 12. Controlled A/B/C/D experiment

E09 definition:

- **A:** exact baseline IDs/counts/sizes/positions/rotations/order.
- **B:** rotations changed only.
- **C:** positions changed only; rotations restored to A.
- **D:** exact transforms preserved, placement list order reversed.

Fixture generator:

```text
scripts/generate_jpeg_experiment_fixtures.py
```

Canonical starting fixture:

```text
research/jpeg-pipeline/fixtures/base_two_piece.json
```

Results:

```text
A: UNKNOWN
B: UNKNOWN
C: UNKNOWN
D: UNKNOWN
```

Do not fill until native saved JPEGs and model-signature evidence exist.

## 13. Current Barro's placement algorithm — separate from stock native behavior

Classification: `PROVEN_FROM_SOURCE` for the Barro's plugin implementation, **not** the stock manual placement algorithm.

Reference:

`docs/CURRENT_PIZZA_PLACEMENT_ALGORITHM_REFERENCE.md`

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

## 14. Research-backed enhanced algorithm candidate

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

Research basis is documented in:

`docs/RESEARCH_BACKED_PLACEMENT_AND_JPEG_GUIDE.md`

## 15. Native reuse / improvement decision

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

## 16. Completion checklist

The notebook may change status to `CHARACTERIZED` only after all required gates in:

`contracts/jpeg-reverse-engineering.acceptance.json`

are PASS with retained evidence.

Until then this heading must remain:

**PARTIALLY CHARACTERIZED — DO NOT CALL COMPLETE**
