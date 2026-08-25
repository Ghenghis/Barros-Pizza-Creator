# PC3 Pizza Creator Native JPEG Research Pipeline

**Scope:** PC3 Pizza Creator only  
**Owner:** Claude  
**Runtime:** `creator-0.11.272`

This folder is the research workspace for determining how the stock Pizza Creator turns an exact `PizzaModel` into its saved pizza image/JPEG.

## Fastest execution order

### Phase A — static work; can run before live runtime is complete

1. Read `docs/NATIVE_PIZZA_JPEG_REVERSE_ENGINEERING_ROADMAP.md`.
2. Read `docs/RESEARCH_BACKED_PLACEMENT_AND_JPEG_GUIDE.md`.
3. Run `RUN_JPEG_RESEARCH_LAB.bat`.
4. Choose **Setup / Verify Research Tools**.
5. Choose **Trace Decompiled Save → JPEG Source** and point it at the exact Creator 0.11.272 decompiled C# root.
6. Review `candidate-methods.csv`, `hits.csv`, and `probable-call-references.csv` in ILSpy.
7. Mark only source-proven findings in `docs/NATIVE_PIZZA_JPEG_ALGORITHM.md`.

Static target gates: `JRE-001`, `JRE-002`, and any source-proven portions of JRE-003..005.

### Phase B — implement exact-placement research harness

Follow:

`docs/NATIVE_JPEG_EXPERIMENT_HARNESS_SPEC.md`

Use:

`contracts/native-jpeg-fixture.schema.json`

Canonical starting fixtures live in:

`research/jpeg-pipeline/fixtures/`

The harness must load exact transforms into the existing native `PizzaModel` / `LoadPizzaFromModel` path and must **not** generate the JPEG itself.

### Phase C — baseline native save characterization

Before variable sweeps:

1. save the exact same model at least 3–5 times;
2. retain model signature and native JPEG each time;
3. use `ANALYZE_NATIVE_JPEG_PAIR.bat` for pair comparisons;
4. use **Fingerprint JPEG Encoder Structure** from the research lab on every image;
5. compare DQT/DHT/SOF/APP fingerprints separately from pixels.

If file hashes differ, determine whether decoded pixels, JPEG metadata, encoder structure, or actual render pixels changed.

### Phase D — controlled geometry experiments

Machine experiment definitions:

`contracts/jpeg-experiment-plan.json`

Generate variants with:

`scripts/generate_jpeg_experiment_fixtures.py`

The generator writes a `.diff-proof.json` next to every fixture and fails if unexpected fields changed.

Recommended order:

1. E01 — rotation
2. E02 — X sweep
3. E03 — Z sweep
4. E04 — Y sweep
5. E07 — size
6. E05 — overlap/order
7. E09 — A/B/C/D same ingredients
8. E08 — dough shape
9. E10 — save/reload image determinism

### Phase E — mathematical inference

#### Camera/framing

Collect CSV:

```csv
label,x,z,u,v
p0,-5.0,0.0,112,244
...
```

Run:

`scripts/fit_jpeg_camera_mapping.py`

Compare affine vs projective homography held-out residuals.

#### Rotation transfer

Collect CSV:

```csv
label,yaw_degrees,image
r0,0,r0.jpg
r45,45,r45.jpg
...
```

Use a matching minimal/background JPEG and run:

`scripts/fit_jpeg_orientation_transfer.py`

Use an asymmetric ingredient. Rotationally symmetric ingredients cannot prove yaw transfer.

### Phase F — runtime source confirmation

Once static candidates are known:

- use dnSpyEx tracepoints/breakpoints on save/render/image methods;
- retain live call stacks and argument values;
- use RenderDoc only when camera/render-target/draw-state facts remain unresolved;
- bind runtime findings to exact Creator build hashes/profile.

### Phase G — final algorithm and design decision

Fill:

`docs/NATIVE_PIZZA_JPEG_ALGORITHM.md`

Every component must remain classified as one of:

```text
PROVEN_FROM_SOURCE
PROVEN_FROM_RUNTIME
INFERRED_AND_VALIDATED
UNKNOWN
```

Only after stock behavior is characterized decide among:

```text
NATIVE_MATCH
NATIVE_CONTROLLED_CAPTURE
ENHANCED_DETERMINISTIC placement
INDEPENDENT_REPLICA (last resort)
```

## Primary scripts

- `scripts/trace_native_jpeg_source.py`
- `scripts/generate_jpeg_experiment_fixtures.py`
- `scripts/analyze_jpeg_experiment.py`
- `scripts/fingerprint_jpeg_encoder.py`
- `scripts/fit_jpeg_camera_mapping.py`
- `scripts/fit_jpeg_orientation_transfer.py`

## Windows launchers

- `RUN_JPEG_RESEARCH_LAB.bat`
- `DOWNLOAD_JPEG_RESEARCH_TOOLS.bat`
- `ANALYZE_NATIVE_JPEG_PAIR.bat`

## Truth contract

`contracts/jpeg-reverse-engineering.acceptance.json`

Research evidence does not automatically promote the main Creator RC1 runtime contract. The same native action may support both only when each contract's own evidence requirements are satisfied.
