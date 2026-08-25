# SCOPE: PC3 PIZZA CREATOR ONLY — Claude Native JPEG Research Start Here

**Owner:** Claude — PC3 Pizza Creator native executor/source-side research  
**Runtime:** `creator-0.11.272`  
**Independent stimulus/verification/observation owner:** ChatGPT-owned Runtime Proof Studio  
**Certified Studio research-control baseline:** `f822de627b3391c8639b74a8b4b72043e101b678`  
**Status:** research architecture ready; stock/native JPEG algorithm remains **PARTIALLY CHARACTERIZED** until retained runtime/source evidence closes the JRE contract.

The Studio baseline above is a known-good interoperability reference, not a permanent pin. Before a live campaign, verify current Studio `main` is clean/green and still exposes the same shared contracts rather than resetting Studio to an old SHA.

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

## 2. One controlled-experiment authority, two shared contracts

Do **not** create a Creator-side E00–E10 generator, observer, campaign ledger, or replacement JPEG writer.

Shared controlled input:

```text
contracts/creator-controlled-stimulus.schema.json
```

Shared Creator execution receipt:

```text
contracts/creator-controlled-execution-evidence.schema.json
```

Creator and Studio copies of both contracts must remain semantically identical.

Studio canonical generator:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/scripts/generate_creator_controlled_stimuli.py
```

Studio canonical observer/verifier:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/CAPTURE_CREATOR_CANONICAL_STIMULUS.bat
```

The Studio generator produces 60 controlled E00–E10 cases with constant model names inside one-variable sweeps so model name cannot become a hidden native-save/JPEG confound.

## 3. Use Studio's certified campaign control plane — do not manually assemble E00–E10

Studio owns the resumable campaign shell. Claude consumes it read-only while owning only the Creator native executor and execution receipt.

Primary Studio entry point:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/CREATOR_JPEG_RESEARCH_CONTROL_PANEL.bat
```

It exposes:

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

`GENERATE_CREATOR_CANONICAL_STIMULI.bat` uses Studio's one canonical generator, then seals:

```text
per-case exact stimulus SHA-256
shared stimulus-schema SHA-256
deterministic whole-corpus SHA-256
```

Default PC3 evidence location:

```text
S:\Unity_Games\PC3\_ecosystem-evidence\creator-jpeg-stimuli\canonical-e00-e10
```

The seal proves input bytes only. It is not runtime proof.

### Resume / next case

Use:

```text
RUN_NEXT_CREATOR_JPEG_CASE.bat
```

Studio:

1. reads the exact sealed campaign ledger;
2. selects the next case below `fully_bound`;
3. verifies the exact stimulus SHA;
4. retains BEFORE UserData;
5. asks Claude's Creator executor to apply the exact stimulus/native operations and retain the execution receipt;
6. retains AFTER stock UserData/JPEG deltas;
7. independently verifies Claude's receipt against the exact stimulus/model/order/actions/assembly;
8. performs Studio analysis plus independent Creator-parser cross-check;
9. refreshes campaign status even when the case remains unresolved.

### Campaign status

Use:

```text
CREATOR_JPEG_CAMPAIGN_STATUS.bat
```

States:

```text
not_run
observed
cross_validated
fully_bound
unresolved
mismatch
```

`cross_validated` means stock-output observation + independent JPEG parser agreement, but the exact Creator execution binding is absent/not PASS.

`fully_bound` means:

```text
exact sealed stimulus
+
Studio-verified exact Creator execution receipt/model/actions/assembly
+
stock output observation
+
independent Studio/Creator JPEG parser agreement
```

Only evidence matching the current exact experiment/case/profile/stimulus SHA can satisfy the current case. Stale corpus revisions remain visible but never count.

### JRE controlled-input readiness

Use:

```text
CREATOR_JPEG_JRE_READINESS.bat
```

Mapped JRE inputs become ready only when every required canonical case is `fully_bound`. The board **never edits or promotes** the Claude-owned JRE acceptance contract; source/runtime/conclusion evidence remains separate.

Studio MCP v1.2 also exposes read-only status surfaces:

```text
pc3_creator_jpeg_campaign_status
pc3_creator_jpeg_next_case
pc3_creator_jpeg_jre_readiness
```

These tools select/report only. They do not launch Creator, mutate the campaign, or promote a JRE gate.

## 4. Claude's unique implementation task

Implement the **exact-model stimulus executor** and **execution receipt producer** in Creator.

Execution path:

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
 -> inspect actual loaded model
 -> native SaveCurrentPizzaToRecipes when requested
 -> native recipe-book reload exact model when requested
 -> native re-save only after exact reload verification when requested
 -> emit shared Creator execution-evidence receipt
```

For every attempted canonical case, emit one receipt conforming exactly to:

```text
contracts/creator-controlled-execution-evidence.schema.json
```

It must include:

```text
experiment_id / case_id
exact stimulus SHA-256
Creator repo SHA
exact Assembly-CSharp SHA-256
actual observed model name/shape/profit
actual placement ARRAY ORDER
actual IDs/sizes/enum values/positions/rotations
requested / attempted / success state for Preview, Save, reload verify, re-save
actual reloaded model when reload verification was requested
```

Do not merely copy the stimulus into `observed_model`; inspect the actual constructed/loaded native model.

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

Use ILSpy to verify lexical/call relationships; dnSpyEx for actual live call stacks/arguments. Use RenderDoc only when camera/render-target/draw/depth state remains unresolved.

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

`case_id` and `notes` are evidence labels, not substantive model changes. If unexpected substantive fields change, do not adjudicate the pair as a one-variable experiment.

Studio's canonical generator is regression-tested for constant model names within one-variable sweeps.

## 7. Three independent evidence links

### A. Controlled input — Studio

Sealed stimulus/corpus identity proves exactly what was requested.

### B. Actual Creator execution — Claude produces, Studio verifies

Claude emits:

```text
creator-controlled-execution-evidence.schema.json
```

Studio independently verifies it with:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/scripts/verify_creator_controlled_execution.py
```

A missing/wrong receipt keeps the case below `fully_bound` and canonical Studio capture uses exit code `5`.

### C. Stock output — Studio independently observes

Studio retains:

```text
exact Creator assembly identity
before UserData tree
after UserData tree
changed/created stock JPEGs
codec fingerprint
pixel differential
DCT differential
single-piece centroid/orientation measurement where applicable
```

It then cross-validates each retained native JPEG using Studio and Creator parsers independently. Parser disagreement uses canonical exit code `4`; missing expected native output uses exit code `3`.

A Creator Save receipt reporting success never substitutes for the stock UserData observation.

## 8. Native JPEG analysis layers

Creator independent tools:

```text
scripts/analyze_jpeg_experiment.py
scripts/fingerprint_jpeg_encoder.py
scripts/fit_jpeg_camera_mapping.py
scripts/fit_jpeg_orientation_transfer.py
```

Studio automatic/standalone parser cross-validation:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/CROSS_VALIDATE_CREATOR_JPEG_FINGERPRINT.bat
```

If independent parsers disagree on file hash, SOF/component sampling, DQT, DHT, restart interval, metadata fingerprints, or IJG quality-family candidates, keep the disputed fact unresolved.

Parser agreement is structural evidence only, not implementation identity.

## 9. Mathematical tests

### Camera/framing

Canonical fully-bound E02/E03 provide known X/Z and proven executed-model transforms. Studio's primary pixel measurement supplies centroid/bounds/PCA. Compare affine vs projective homography; source/runtime still determines the actual Unity Camera path.

Creator independent fitter:

```text
scripts/fit_jpeg_camera_mapping.py
```

### Rotation

Fully-bound E01 holds the substantive model constant except yaw. Use Studio's component/PCA measurement plus Creator's independent:

```text
scripts/fit_jpeg_orientation_transfer.py
```

Use a visibly asymmetric topping; rotationally symmetric toppings cannot prove yaw transfer.

## 10. JPEG encoder forensics

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

Do not identify the encoder implementation from DQT similarity alone.

## 11. Online/paper-backed enhanced placement research

Read:

```text
docs/RESEARCH_BACKED_PLACEMENT_AND_JPEG_GUIDE.md
```

Optional enhanced route after stock characterization:

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

Research families include Bridson, Yuksel, capacity-constrained/optimal-transport blue noise, anisotropic/shaped sampling, Vogel golden angle, Zhang calibration, SSIM, Kornblum quantization fingerprints, and Cogranne standard JPEG quality-factor determination.

Do not replace stock behavior until stock behavior is characterized and `NATIVE_MATCH` remains available.

## 12. Fastest research order

```text
A. finish Creator exact-model executor + execution receipt
B. static save->render->JPEG source trace in parallel
C. Studio generate + seal canonical E00-E10 corpus
D. use RUN_NEXT_CREATOR_JPEG_CASE.bat repeatedly and supply the receipt for every case
E. reach fully_bound, not merely parser cross_validated
F. E00 repeated identical native saves
G. E01 rotation
H. E02/E03 camera mapping
I. E04/E05 depth/order
J. E07 size footprint
K. E08 dough shape/framing
L. E09 A/B/C/D controlled differential
M. E10 native save/reload/re-save determinism
N. use campaign status + JRE input-readiness boards
O. confirm static candidates with dnSpyEx/RenderDoc
P. fill NATIVE_PIZZA_JPEG_ALGORITHM.md
Q. decide native reuse vs controlled capture vs optional enhanced placement
```

## 13. Completion rule

Do not call the native image/JPEG algorithm complete until every required gate in:

```text
contracts/jpeg-reverse-engineering.acceptance.json
```

is supported by retained evidence and `docs/NATIVE_PIZZA_JPEG_ALGORITHM.md` no longer has unresolved required `UNKNOWN` components.

Even a Studio `fully_bound 60/60` campaign means the controlled stimulus → actual Creator execution → stock output evidence layer is complete. It does **not** replace required source/runtime call-chain proof or automatically set a JRE gate to PASS.
