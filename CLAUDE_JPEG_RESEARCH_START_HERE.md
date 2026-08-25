# SCOPE: PC3 PIZZA CREATOR ONLY — Claude Native JPEG Research Start Here

**Owner:** Claude — PC3 Pizza Creator native executor/source-side research  
**Runtime:** `creator-0.11.272`  
**Independent stimulus producer/observer:** ChatGPT-owned Runtime Proof Studio  
**Certified Studio research-control baseline:** `f822de627b3391c8639b74a8b4b72043e101b678`  
**Status:** research architecture ready; stock/native JPEG algorithm remains **PARTIALLY CHARACTERIZED** until retained runtime evidence closes the JRE contract.

The Studio baseline above is a known-good interoperability reference, not a permanent pin. Before a live campaign, verify current Studio `main` is clean/green and still exposes the same shared stimulus contract rather than resetting Studio to an old SHA.

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

Do **not** create a Creator-side E00–E10 generator, observer, campaign ledger, or replacement JPEG writer.

Shared schema:

```text
contracts/creator-controlled-stimulus.schema.json
```

Creator and Studio copies must remain semantically identical.

Studio canonical generator:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/scripts/generate_creator_controlled_stimuli.py
```

Studio canonical observer:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/CAPTURE_CREATOR_CANONICAL_STIMULUS.bat
```

The Studio generator produces 60 controlled E00–E10 cases with constant model names inside one-variable sweeps so model name cannot become a hidden native-save/JPEG confound.

## 3. Use Studio's certified campaign control plane — do not manually assemble E00–E10

Studio now owns the complete resumable campaign shell. Claude consumes it read-only while owning only the Creator native executor.

Primary Studio entry point:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/CREATOR_JPEG_RESEARCH_CONTROL_PANEL.bat
```

The control panel exposes:

```text
GENERATE_CREATOR_CANONICAL_STIMULI.bat
RUN_NEXT_CREATOR_JPEG_CASE.bat
CAPTURE_CREATOR_CANONICAL_STIMULUS.bat
CREATOR_JPEG_CAMPAIGN_STATUS.bat
CREATOR_JPEG_JRE_READINESS.bat
CROSS_VALIDATE_CREATOR_JPEG_FINGERPRINT.bat
INSTALL_CREATOR_JPEG_RESEARCH_TOOLS.bat
CAPTURE_CREATOR_JPEG_FORENSICS.bat
```

### Canonical corpus identity

`GENERATE_CREATOR_CANONICAL_STIMULI.bat` uses Studio's one canonical generator, then seals the emitted corpus with:

```text
per-case exact stimulus SHA-256
shared schema SHA-256
deterministic whole-corpus SHA-256
```

Default PC3 evidence location:

```text
S:\Unity_Games\PC3\_ecosystem-evidence\creator-jpeg-stimuli\canonical-e00-e10
```

The seal proves stimulus bytes only. It is not native runtime proof.

### Resume / next case

Use:

```text
RUN_NEXT_CREATOR_JPEG_CASE.bat
```

rather than manually choosing the next case. Studio:

1. reads the current sealed campaign ledger;
2. selects the next case needing attention;
3. verifies that exact stimulus file still matches its sealed SHA-256;
4. retains BEFORE UserData;
5. asks Claude's Creator executor to apply that exact stimulus and requested native operation;
6. retains AFTER UserData/native JPEG deltas;
7. performs Studio analysis plus independent Creator-parser cross-check;
8. refreshes campaign status even when the case remains unresolved.

### Campaign status

Use:

```text
CREATOR_JPEG_CAMPAIGN_STATUS.bat
```

Case states:

```text
not_run
observed
cross_validated
unresolved
mismatch
```

Only evidence matching the exact current:

```text
experiment_id
case_id
creator-0.11.272 profile
stimulus SHA-256
```

can satisfy the current case. Stale corpus revisions remain visible but never count as current completion.

### JRE controlled-input readiness

Use:

```text
CREATOR_JPEG_JRE_READINESS.bat
```

This shows which JRE questions now have all mapped E00–E10 controlled-output inputs available. It **never edits or promotes** the Claude-owned JRE acceptance contract. Source/runtime/conclusion evidence remains separately required.

Studio MCP v1.2 also exposes read-only agent surfaces:

```text
pc3_creator_jpeg_campaign_status
pc3_creator_jpeg_next_case
pc3_creator_jpeg_jre_readiness
```

These tools select/report only. They do not launch Creator, mutate the campaign, or promote a JRE gate.

## 4. Claude's unique implementation task

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
- create a competing campaign/status ledger;
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

## 5. Static source research Claude can do before live experiments

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

## 6. One-variable input proof

Before interpreting an A/B pair, use:

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

If unexpected substantive fields change, do not adjudicate the pair as a one-variable experiment.

Studio's canonical generator is also regression-tested for constant model names within one-variable sweeps.

## 7. Native JPEG analysis layers

### Primary independent observation — Studio

Studio's canonical observer retains:

```text
exact stimulus SHA
experiment_id / case_id
exact Creator assembly identity
before UserData tree
stock native operation
after UserData tree
changed/created JPEGs
codec fingerprint
pixel differential
DCT differential
single-piece centroid/orientation measurement where applicable
```

The canonical wrapper retains the base observation first, then independently cross-validates each observed native JPEG using both Studio and Creator parsers.

### Creator independent cross-check

Creator-side tools:

```text
scripts/analyze_jpeg_experiment.py
scripts/fingerprint_jpeg_encoder.py
scripts/fit_jpeg_camera_mapping.py
scripts/fit_jpeg_orientation_transfer.py
```

Studio automatic/standalone cross-validation:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/CROSS_VALIDATE_CREATOR_JPEG_FINGERPRINT.bat
```

If independent parsers disagree on file hash, SOF/component sampling, DQT, DHT, restart interval, metadata fingerprints, or IJG quality-family candidates, keep the disputed forensic fact unresolved.

Parser agreement proves only common JPEG structural observations. It does not prove the native Unity writer/camera/save call chain.

## 8. Mathematical tests

### Camera/framing

Canonical E02/E03 produce known X/Z stimuli.

Studio's primary pixel measurement uses noise-aware component isolation and measured centroid/bounds/PCA. Fit:

```text
affine mapping
vs
projective homography
```

Creator-side independent fitter:

```text
scripts/fit_jpeg_camera_mapping.py
```

Held-out residuals provide inference about whether capture behaves approximately affine/orthographic-like or requires projective mapping. Source/runtime evidence still decides the actual Unity Camera path.

### Rotation

Canonical E01 holds the model constant except Y yaw.

Use Studio's automatic component/PCA measurement as the primary observation. Creator's:

```text
scripts/fit_jpeg_orientation_transfer.py
```

can independently fit native yaw -> image axial orientation.

Use a visibly asymmetric topping; rotationally symmetric toppings cannot prove yaw transfer.

## 9. JPEG encoder forensics

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

## 10. Online/paper-backed enhanced placement research

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

## 11. Fastest research order

```text
A. finish Creator exact-model stimulus executor
B. static save->render->JPEG source trace in parallel
C. Studio generate + seal canonical E00-E10 corpus
D. use RUN_NEXT_CREATOR_JPEG_CASE.bat repeatedly; do not hand-pick around unresolved cases silently
E. E00 repeated identical native saves
F. E01 rotation
G. E02/E03 camera mapping
H. E04/E05 depth/order
I. E07 size footprint
J. E08 dough shape/framing
K. E09 A/B/C/D controlled differential
L. E10 native save/reload/re-save determinism
M. use campaign status + JRE input-readiness boards
N. confirm static candidates with dnSpyEx/RenderDoc
O. fill NATIVE_PIZZA_JPEG_ALGORITHM.md
P. decide native reuse vs controlled capture vs optional enhanced placement
```

## 12. Completion rule

Do not call the native image/JPEG algorithm complete until every required gate in:

```text
contracts/jpeg-reverse-engineering.acceptance.json
```

is supported by retained evidence and `docs/NATIVE_PIZZA_JPEG_ALGORITHM.md` no longer has unresolved required `UNKNOWN` components.

A Studio campaign state of `cross_validated` or even `60/60` means the controlled **observation layer** is complete. It does not replace required source/runtime proof or automatically set a JRE gate to PASS.
