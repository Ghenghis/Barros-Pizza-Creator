# SCOPE: PC3 PIZZA CREATOR ONLY — Claude Native JPEG Research Start Here

**Owner:** Claude — PC3 Pizza Creator native executor/source-side research  
**Runtime:** `creator-0.11.272`  
**Independent stimulus producer/observer:** ChatGPT-owned Runtime Proof Studio  
**Status:** research architecture ready; stock/native JPEG algorithm remains **PARTIALLY CHARACTERIZED** until retained runtime evidence closes the JRE contract.

## 1. Do not rediscover the architecture

Read in this order:

1. `00_READ_FIRST_PC3_ONLY.md`
2. `CLAUDE_HANDOFF.md`
3. `docs/CLAUDE_METHOD_FILE_IMPLEMENTATION_ATLAS.md`
4. `docs/NATIVE_PIZZA_JPEG_REVERSE_ENGINEERING_ROADMAP.md`
5. `docs/NATIVE_JPEG_EXPERIMENT_HARNESS_SPEC.md`
6. `research/jpeg-pipeline/README.md`
7. `docs/NATIVE_PIZZA_JPEG_ALGORITHM.md`

Research truth:

```text
contracts/jpeg-reverse-engineering.acceptance.json
```

Main Creator runtime truth remains separate:

```text
contracts/rc1.acceptance.json
```

## 2. One controlled-experiment authority

Do **not** create a Creator-side E00–E10 generator.

Shared schema:

```text
contracts/creator-controlled-stimulus.schema.json
```

Studio canonical generator:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/scripts/generate_creator_controlled_stimuli.py
```

Studio canonical observer:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/CAPTURE_CREATOR_CANONICAL_STIMULUS.bat
```

The Studio generator produces 60 controlled E00–E10 cases with constant model names inside each sweep so model name cannot become a hidden native-save/JPEG confound.

## 3. Claude's unique implementation task

Implement the **exact-model stimulus executor** in Creator.

It must:

```text
shared controlled stimulus
 -> strict validate creator-0.11.272
 -> exact model.name / shape / profit_factor
 -> exact placement ARRAY ORDER
 -> exact installed ingredient ID + size
 -> exact position x/y/z
 -> exact rotation x/y/z
 -> native GetPizzaShape(...).DoughPositions
 -> real PizzaModel / IngredientContainerModel
 -> native LoadPizzaFromModel
 -> native SaveCurrentPizzaToRecipes when requested
 -> native recipe-book reload exact ModelSignature when requested
 -> native re-save only after exact reload verification when requested
```

It must **not**:

- run the Barro's golden-angle placement generator for controlled stimuli;
- encode/create/patch the JPEG;
- create a competing evidence root;
- edit Studio/Workbench implementation.

Implementation spec:

```text
docs/NATIVE_JPEG_EXPERIMENT_HARNESS_SPEC.md
```

Primary code anchors:

```text
plugin-src/GameBridge.cs
plugin-src/BarrosAiPlugin.cs
plugin-src/PanelRenderer.cs
plugin-src/Models.cs
plugin-src/EvidenceRecorder.cs
```

## 4. Static source research Claude can do before live experiments

Run:

```text
RUN_JPEG_RESEARCH_LAB.bat
```

Then:

```text
Setup / Verify Research Tools
Trace Decompiled Save → JPEG Source
```

Static tracer:

```text
scripts/trace_native_jpeg_source.py
```

Search/rank targets include:

```text
SaveCurrentPizzaToRecipes
EncodeToJPG / JPEG
ReadPixels
RenderTexture / targetTexture
Camera.Render
Graphics.Blit
File.WriteAllBytes / FileStream
.jpg / .jpeg
thumbnail / recipe-image terms
storage/path APIs
save/event publishing
```

Use ILSpy to verify lexical/call relationships; use dnSpyEx for actual live call stacks/arguments. Use RenderDoc only when render target/draw/depth/camera state remains unresolved.

## 5. One-variable input proof

Before interpreting an A/B pair, run:

```text
scripts/compare_controlled_stimuli.py
```

Examples:

```text
E01 allow model.placements[*].rotation.y
E02 allow model.placements[*].position.x
E03 allow model.placements[*].position.z
E04 allow model.placements[*].position.y
```

`case_id` and `notes` are evidence labels, not substantive model changes.

If unexpected substantive fields change, do not run/adjudicate the pair as a one-variable experiment.

## 6. Native JPEG analysis layers

### Primary independent observation — Studio

Studio's canonical observer retains:

```text
exact stimulus SHA
experiment_id / case_id
exact Creator assembly identity
before UserData tree
stock native operation
post-operation UserData tree
changed/created JPEGs
codec fingerprint
pixel differential
DCT differential
single-piece centroid/orientation measurement where applicable
```

### Creator independent cross-check

Creator-side tools:

```text
scripts/analyze_jpeg_experiment.py
scripts/fingerprint_jpeg_encoder.py
scripts/fit_jpeg_camera_mapping.py
scripts/fit_jpeg_orientation_transfer.py
```

Studio can cross-validate its parser against Creator's parser with:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/CROSS_VALIDATE_CREATOR_JPEG_FINGERPRINT.bat
```

If the two independent parsers disagree on file hash, SOF/component sampling, DQT, DHT, restart interval, metadata fingerprints, or IJG quality-family candidates, keep the disputed forensic fact unresolved.

## 7. Mathematical tests

### Camera/framing

Canonical E02/E03 produce known X/Z stimuli.

Collect measured piece centroids and fit:

```text
affine mapping
vs
projective homography
```

with:

```text
scripts/fit_jpeg_camera_mapping.py
```

Held-out residuals provide inference about whether the capture behaves approximately affine/orthographic-like or requires projective mapping. Source/runtime evidence still decides the actual Unity Camera path.

### Rotation

Canonical E01 holds the model constant except Y yaw.

Use Studio's automatic component/PCA measurement as the primary observation. Creator's `fit_jpeg_orientation_transfer.py` can independently fit native yaw -> image axial orientation.

Use a visibly asymmetric topping; rotationally symmetric toppings cannot prove yaw transfer.

## 8. JPEG encoder forensics

Read:

```text
docs/JPEG_ENCODER_FORENSICS_GUIDE.md
```

Evidence ladder:

```text
file hash
 -> decoded pixels
 -> DQT/DHT/SOF/sampling/APP structure
 -> exact IJG quality-family candidate if applicable
 -> static source API identity
 -> live runtime call identity
```

Do not call the encoder `libjpeg`, `Unity EncodeToJPG`, or anything else from DQT similarity alone.

## 9. Online/paper-backed enhanced placement research

Read:

```text
docs/RESEARCH_BACKED_PLACEMENT_AND_JPEG_GUIDE.md
```

Research-backed optional enhanced route:

```text
real native dough domain
+ exact ingredient footprint
+ deterministic golden-angle/candidate initialization
+ variable/anisotropic Poisson separation
+ sample elimination to exact piece count
+ bounded capacity/Lloyd-style relaxation
+ ingredient-aware deterministic orientation
+ measured native-compatible layer ordering
+ explicit transforms
+ native PizzaModel
+ native renderer
+ native JPEG generator whenever possible
```

Key literature families:

- Bridson Poisson-disk sampling;
- Yuksel sample elimination;
- Balzer/Schlömer/Deussen capacity-constrained Lloyd;
- de Goes et al. optimal-transport blue noise;
- Li/Wei/Sander/Fu anisotropic blue noise;
- Wang/Hu/Urahama shaped anisotropic pieces;
- Vogel golden-angle/phyllotaxis;
- Zhang planar camera calibration;
- Wang/Bovik/Sheikh/Simoncelli SSIM;
- Kornblum JPEG quantization-table software fingerprints;
- Cogranne exact standard JPEG quality-factor determination.

Do not replace stock behavior with this enhanced algorithm until stock behavior is characterized and `NATIVE_MATCH` remains available.

## 10. Fastest research order

```text
A. finish Creator exact-model stimulus executor
B. static save->render->JPEG source trace in parallel
C. E00 repeated identical native saves
D. E01 rotation
E. E02/E03 camera mapping
F. E04/E05 depth/order
G. E07 size footprint
H. E08 dough shape/framing
I. E09 A/B/C/D user experiment
J. E10 native save/reload/re-save determinism
K. confirm static candidates with dnSpyEx/RenderDoc
L. fill NATIVE_PIZZA_JPEG_ALGORITHM.md
M. decide native reuse vs controlled capture vs optional enhanced placement
```

## 11. Completion rule

Do not call the native image/JPEG algorithm complete until every required gate in:

```text
contracts/jpeg-reverse-engineering.acceptance.json
```

is supported by retained evidence and `docs/NATIVE_PIZZA_JPEG_ALGORITHM.md` no longer has unresolved required `UNKNOWN` components.
