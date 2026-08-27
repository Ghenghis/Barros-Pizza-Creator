# PC3 Pizza Creator Native JPEG Research Pipeline

> **Reduced scope as of 2026-08-27.** The static exporter is proven and there is no embedded editable-recipe codec to recover. Use this pipeline only for live pixel, framing, placement, occlusion, repeatability, and encoder-output confirmation.

**Scope:** PC3 Pizza Creator only  
**Creator owner/executor:** Claude  
**Studio stimulus producer/observer:** ChatGPT-owned Runtime Proof Studio  
**Runtime:** `creator-0.11.272`

This folder documents the shortest evidence-safe route for determining how the stock Pizza Creator turns an exact `PizzaModel` into its saved pizza image/JPEG.

## One experimental truth path

Use exactly this chain:

```text
Studio canonical E00-E10 generator
  -> shared creator-controlled-stimulus contract
  -> Claude Creator exact-model executor
  -> native LoadPizzaFromModel
  -> native Save / reload / re-save
  -> stock Creator UserData/JPEG
  -> Studio independent controlled observer
  -> Creator/Studio analysis tools
  -> JRE acceptance contract + final algorithm notebook
```

Do not create a second stimulus schema or Creator-side corpus generator.

Shared contract:

```text
contracts/creator-controlled-stimulus.schema.json
```

Canonical Studio generator:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/scripts/generate_creator_controlled_stimuli.py
```

Studio controlled observer launcher:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/CAPTURE_CREATOR_CONTROLLED_JPEG_EXPERIMENT.bat
```

The Creator lab may read/run those Studio-owned surfaces; it does not edit them.

## Fastest execution order

### Phase A — static work

Can begin as soon as Creator housekeeping is stable.

1. Read `docs/NATIVE_PIZZA_JPEG_REVERSE_ENGINEERING_ROADMAP.md`.
2. Read `docs/RESEARCH_BACKED_PLACEMENT_AND_JPEG_GUIDE.md`.
3. Run `RUN_JPEG_RESEARCH_LAB.bat`.
4. Choose **Setup / Verify Research Tools**.
5. Choose **Trace Decompiled Save → JPEG Source** against the exact Creator 0.11.272 decompiled C# root.
6. Review `candidate-methods.csv`, `hits.csv`, and `probable-call-references.csv` in ILSpy.
7. Confirm promising methods with dnSpyEx/live trace when runtime is available.
8. Write only source/runtime-proven findings into `docs/NATIVE_PIZZA_JPEG_ALGORITHM.md`.

Static target gates: JRE-001, JRE-002, and source-resolvable parts of JRE-003..005.

### Phase B — implement Claude's exact-model executor

Follow:

```text
docs/NATIVE_JPEG_EXPERIMENT_HARNESS_SPEC.md
```

The executor must:

- accept the shared controlled stimulus schema;
- preserve placement array order exactly;
- bind exact IDs/sizes/positions/rotations directly into real `PizzaModel`/`IngredientContainerModel` objects;
- obtain native dough positions from `IDatabaseService.GetPizzaShape()`;
- call `IPizzaCreatorService.LoadPizzaFromModel()`;
- invoke only the native recipe-book save path when requested;
- perform native reload exact-model verification when requested;
- never generate/encode/rewrite the research JPEG itself.

### Phase C — generate canonical stimuli

From `RUN_JPEG_RESEARCH_LAB.bat`, choose:

```text
Generate Canonical Studio Stimuli
```

That button locates or prompts for the **read-only Studio repository** and invokes Studio's canonical 60-case E00-E10 generator.

Studio's generator is regression-tested so model names remain constant within controlled sweeps. `case_id`/`notes` serve as evidence labels and must not become native model differences.

### Phase D — prove one-variable inputs

Before adjudicating an A/B experiment, use:

```text
scripts/compare_controlled_stimuli.py
```

Examples:

E01 rotation-only:

```text
--allow "model.placements[*].rotation.y"
```

E02 X-only:

```text
--allow "model.placements[*].position.x"
```

The comparator separates `case_id`/`notes` evidence labels from substantive model/operation changes and fails closed when an unexpected substantive field changes.

### Phase E — baseline native-save characterization

Start with E00.

1. apply/save the identical model at least 3 times;
2. let Studio retain before/after native UserData/image observations;
3. bind each native image to exact stimulus SHA + Creator model signature;
4. compare pairs with `ANALYZE_NATIVE_JPEG_PAIR.bat`;
5. fingerprint encoder structure with `scripts/fingerprint_jpeg_encoder.py`;
6. separate:
   - exact byte variation;
   - decoded-pixel variation;
   - DQT/DHT/SOF/sampling variation;
   - APP/COM metadata variation.

### Phase F — controlled geometry experiments

Machine plan:

```text
contracts/jpeg-experiment-plan.json
```

Canonical experiments come from Studio's generator:

1. E01 — rotation sweep
2. E02 — X sweep
3. E03 — Z sweep
4. E04 — Y/depth sweep
5. E05 — overlap/order factorial
6. E06 — piece-count/density sweep with explicit fixed-prefix transforms
7. E07 — Large/Medium/Small
8. E08 — Round/Square/Star/Triangle
9. E09 — same ingredients A/B/C/D: baseline / rotation-only / position-only / order-only
10. E10 — native save -> native reload exact model -> native re-save

### Phase G — mathematical inference

#### Camera/framing

Collect:

```csv
label,x,z,u,v
```

Run:

```text
scripts/fit_jpeg_camera_mapping.py
```

It fits affine and normalized projective homography models and compares held-out residuals. This is mathematical guidance, not source/runtime camera proof.

#### Rotation transfer

Collect:

```csv
label,yaw_degrees,image
```

Run:

```text
scripts/fit_jpeg_orientation_transfer.py
```

Use an asymmetric topping and a matching baseline/background JPEG.

### Phase H — JPEG encoder forensics

Use:

```text
scripts/fingerprint_jpeg_encoder.py
```

It records DQT/DHT/SOF/APP/COM/restart/scan fingerprints and exact IJG standard quality-family matches when applicable.

Read:

```text
docs/JPEG_ENCODER_FORENSICS_GUIDE.md
```

A quantization-table quality match is a forensic fingerprint, not proof of encoder implementation. Confirm actual API/library with static/live tracing.

### Phase I — runtime source confirmation

Once static candidates are known:

- use dnSpyEx tracepoints/breakpoints on confirmed save/render/image methods;
- retain actual call stacks and arguments;
- use AssetRipper for camera/prefab/material inventory;
- use RenderDoc when camera/render-target/draw-order/depth state remains unresolved;
- bind all runtime findings to exact Creator profile/assembly identity.

### Phase J — final algorithm and design decision

Fill:

```text
docs/NATIVE_PIZZA_JPEG_ALGORITHM.md
```

Classify every component as:

```text
PROVEN_FROM_SOURCE
PROVEN_FROM_RUNTIME
INFERRED_AND_VALIDATED
UNKNOWN
```

Only after stock behavior is characterized choose among:

```text
NATIVE_MATCH
NATIVE_CONTROLLED_CAPTURE
ENHANCED_DETERMINISTIC placement
INDEPENDENT_REPLICA (last resort)
```

## Creator-side primary scripts

- `scripts/trace_native_jpeg_source.py`
- `scripts/compare_controlled_stimuli.py`
- `scripts/analyze_jpeg_experiment.py`
- `scripts/fingerprint_jpeg_encoder.py`
- `scripts/fit_jpeg_camera_mapping.py`
- `scripts/fit_jpeg_orientation_transfer.py`

## Windows launchers

- `RUN_JPEG_RESEARCH_LAB.bat`
- `DOWNLOAD_JPEG_RESEARCH_TOOLS.bat`
- `ANALYZE_NATIVE_JPEG_PAIR.bat`

## Truth contracts

Research truth:

```text
contracts/jpeg-reverse-engineering.acceptance.json
```

Main Creator runtime truth remains:

```text
contracts/rc1.acceptance.json
```

A research observation never silently promotes an RC1 gate, and an RC1 PASS never silently resolves a JPEG-research unknown. Evidence may support both only when both contracts' requirements are independently satisfied.
