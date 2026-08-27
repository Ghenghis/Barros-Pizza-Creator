# SCOPE: PC3 PIZZA CREATOR ONLY — Native Pizza JPEG Reverse-Engineering Roadmap

> **Superseded for exporter/codec discovery (2026-08-27).** The exact path is source-proven in `NATIVE_PIZZA_JPEG_ALGORITHM.md`; the JPG contains no editable recipe payload. Use this roadmap only for remaining live camera, visual-placement, occlusion, and repeatability measurements.

**Owner:** Claude — PC3 Pizza Creator  
**Repository:** `Ghenghis/Barros-Pizza-Creator`  
**Runtime profile:** `creator-0.11.272`  
**Goal:** determine, prove, and document the exact algorithm/path by which the running Pizza Creator turns a real pizza model into the JPEG/image saved for that pizza, including how ingredient placement, rotation, layer order, size, camera, lighting, render target, crop/scale, colorspace, and JPEG encoding affect the final bytes.

This is a reverse-engineering and experiment track. Do not guess the native algorithm from screenshots alone.

## 1. What is already proven

From the exact supplied Creator build and current integration:

- save/model keys include `ID`, `Ingredients`, `DoughPositions`, and `ProfitFactor`;
- each placed ingredient preserves `Ingredient`, `IngredientID`, `Rotation`, `Position`, and `Size`;
- the game can rebuild the real 3D pizza from a `PizzaModel` through `IPizzaCreatorService.LoadPizzaFromModel(PizzaModel)`;
- the game internally places the ingredient objects using the supplied model data;
- native save uses `SaveCurrentPizzaToRecipes()` for the recipe-book operation;
- exact runtime target is Creator `0.11.272`, Unity `2017.3.1p4 x64`.

What is **not yet proven** is the complete native image-generation chain after/beside recipe save.

## 2. Questions this track must answer

Determine with evidence:

1. What method initiates pizza-image generation?
2. Is image generation part of `SaveCurrentPizzaToRecipes()`, a subscriber/event handler, a recipe-card UI refresh, or a separate screenshot/thumbnail service?
3. Does the image come from:
   - a dedicated Camera;
   - the main game camera;
   - a RenderTexture;
   - a UI camera;
   - a preexisting texture/material;
   - a temporary hidden scene/object?
4. Is the pizza re-rendered from the current scene or reconstructed from saved `PizzaModel` data?
5. Which camera transform/FOV/orthographic settings are used?
6. What target resolution is rendered before encoding?
7. Is there crop, resize, letterbox, alpha flattening, or background composition?
8. Which color space/gamma path is used?
9. Which JPEG encoder/API is called?
10. What JPEG quality/subsampling settings are used?
11. Is metadata written?
12. How is the filename/path derived?
13. Does the same model saved twice produce byte-identical JPEGs?
14. Does ingredient list order affect draw/layer order?
15. Does Y layer (`1.0 + n×0.01`) affect occlusion and therefore the JPEG?
16. Does ingredient Y rotation affect visible texture/mesh orientation in the saved image?
17. Do X/Z changes map linearly/perspectively into image pixels?
18. Do ingredient sizes select different meshes/textures or only scale?
19. Are lighting/shadows/time/frame state deterministic?
20. Can the native image algorithm be reproduced exactly outside the game, or should we reuse the native renderer as the authoritative generator?

## 3. Tooling to stage

Use current stable Windows builds from official projects where possible.

### Required

- **ILSpy** — static whole-assembly search/decompilation.
- **dnSpyEx** — live .NET/Unity debugging, breakpoints, call stacks, locals, method tracing.
- **AssetRipper** — inspect Unity assets, cameras, materials, textures, prefabs, shaders, and serialized scene data when needed.
- **ImageMagick** — deterministic image metrics/diff images: RMSE, MAE, PSNR, SSIM, PHASH/NCC.
- **Python + Pillow/OpenCV or equivalent local analysis** — pixel coordinate extraction, feature matching, regression/fitting, JPEG quantization inspection.

### High-value optional

- **RenderDoc** — capture the D3D frame and identify the exact camera/render target/draw calls used when the pizza image is generated.
- existing BepInEx plugin — add minimal instrumentation around discovered methods without replacing the game's algorithm.

Do not download random forks when an official project build exists. Record tool name/version/hash in the experiment evidence.

## 4. Static reverse-engineering search plan

Search the exact 2,681-file decompiled source corpus and assemblies for these families.

### Save/recipe chain

```text
SaveCurrentPizzaToRecipes
GetAllRecipes
PizzaLoaded
PizzaSaved
Recipe
Thumbnail
Preview
Portrait
Snapshot
Screenshot
Image
Picture
Photo
```

### Unity render/image APIs

```text
Texture2D
RenderTexture
Camera.Render
Camera.targetTexture
ReadPixels
GetPixels
EncodeToJPG
EncodeToPNG
ImageConversion
Graphics.Blit
ScreenCapture
WWW
File.WriteAllBytes
FileStream
```

### JPEG/path clues

```text
.jpg
.jpeg
JPG
JPEG
quality
persistentDataPath
streamingAssetsPath
dataPath
Application.persistentDataPath
```

### Dependency tracing

For every match, record:

```text
assembly
namespace
class
method
caller(s)
callee(s)
fields/services used
file paths/constants
Unity object types referenced
```

Build a call graph from user Save action to final file write/texture assignment.

## 5. Dynamic reverse-engineering plan

After static candidates are known:

1. Launch exact Creator build under dnSpyEx/approved instrumentation.
2. Set breakpoints/tracepoints on candidate save/image methods.
3. Create a simple pizza.
4. Trigger native Save.
5. Record call stack and argument values at every image-related method.
6. Record Camera/RenderTexture dimensions/settings.
7. Record any `Texture2D` dimensions before encoding.
8. Record encoder quality argument if present.
9. Record destination path and file bytes/hash.
10. Repeat with the exact same model.
11. Repeat after changing only one variable.

If RenderDoc is used, capture the frame around native image generation and identify:

- render target size/format;
- draw calls for dough and each ingredient;
- mesh/material/shader/texture identities;
- camera matrix;
- blend/depth state;
- lighting/shadow passes;
- final blit/copy before CPU readback.

## 6. Controlled experiment protocol

Every experiment is an A/B pair where **exactly one independent variable changes**.

For every run retain:

```text
PizzaModel JSON/signature
ingredient list/order
all positions
all rotations
sizes
shape
dough positions
profit factor
saved JPEG bytes
JPEG SHA-256
JPEG dimensions
file size
JPEG metadata/quantization information
runtime events/log
native screenshot/reference if useful
```

### Repetition rule

Run every important baseline at least 3 times without changing the model.

If hashes differ, determine whether the variation comes from:

- JPEG encoder nondeterminism/metadata;
- lighting/frame timing;
- stochastic scene state;
- texture/render target state;
- file timestamps/metadata only.

## 7. Experiment matrix

### E00 — empty/minimal baseline

Purpose: isolate dough/background/camera.

- same shape, no optional toppings if game permits;
- save 3 times;
- compare exact bytes and pixels.

### E01 — one ingredient, one piece

Purpose: establish image coordinate mapping and orientation visibility.

- one known asymmetric ingredient if available;
- one piece near center;
- rotations: 0°, 45°, 90°, 135°, 180°, 270°;
- same X/Y/Z.

Measure pixel-space feature orientation.

### E02 — X-axis sweep

Hold everything constant except X.

Suggested positions:

```text
-5.0
-4.0
-3.0
-2.0
-1.0
```

Fit world-X -> image-u mapping.

### E03 — Z-axis sweep

Hold everything constant except Z.

Suggested positions:

```text
-2.0
-1.0
0.0
1.0
2.0
```

Fit world-Z -> image-v mapping.

### E04 — Y/layer sweep

Same X/Z/rotation; alter only Y around the native layer band.

Purpose: determine depth sorting/occlusion sensitivity.

### E05 — two-piece overlap/order test

Create A and B at overlapping positions.

Pairs:

```text
A then B
B then A
same Y
slightly different Y
```

Determine whether list order, Y depth, renderer order, or material queue controls visible stacking.

### E06 — count test

Same ingredient/distribution; increase piece count:

```text
1
2
4
8
16
32
```

Determine whether save/render path changes camera framing, scale, clipping, or compression behavior.

### E07 — size test

Same ingredient/position/rotation with Large, Medium, Small.

Measure visible bounds and texture/mesh identity.

### E08 — shape test

Same topping geometry relative to shape where possible:

```text
Round
Square
Star
Triangle
```

Determine whether camera/framing/background changes with dough shape.

### E09 — identical ingredient set, alternate arrangement

This implements the proposed test directly.

A:

- exact ingredient IDs/counts/sizes;
- deterministic positions/rotations set A;
- native Save -> JPEG A.

B:

- same IDs/counts/sizes/name/profit/shape;
- positions unchanged, rotations changed only;
- native Save -> JPEG B.

C:

- same IDs/counts/sizes/name/profit/shape;
- rotations reset to A, positions changed only;
- native Save -> JPEG C.

D:

- same exact positions/rotations but ingredient list order reversed;
- native Save -> JPEG D.

Compare A/B/C/D using exact hash + RMSE + SSIM + PHASH + visual diff.

### E10 — save/reload determinism

- Save model A.
- Reload through native recipe book.
- Verify model signature.
- Save image again.
- Compare original JPEG vs post-reload JPEG.

This tells us whether image generation depends only on serialized model or on transient scene state.

## 8. Image-analysis outputs

For every A/B pair compute at minimum:

```text
SHA-256 exact equality
width/height
file size
JPEG quantization/subsampling metadata where available
RMSE
SSIM
PHASH distance
pixel difference bounding box
```

For coordinate experiments also compute:

```text
ingredient feature centroid
bounding box
principal orientation angle
world -> image regression coefficients
residual error
```

## 9. Native algorithm extraction target

The final document should be able to describe the native image path as a reproducible function:

```text
JPEG = F(
  PizzaModel,
  ingredient asset/mesh/material mapping,
  placement transform,
  renderer/depth/order rules,
  dough/shape,
  camera matrix,
  lighting/shaders,
  render target,
  crop/resize/colorspace,
  JPEG encoder settings
)
```

For every component classify it as:

```text
PROVEN_FROM_SOURCE
PROVEN_FROM_RUNTIME
INFERRED_AND_VALIDATED
UNKNOWN
```

Do not collapse inferred behavior into proven behavior.

## 10. Improvement decision gate

Do **not** improve the algorithm until the stock behavior is characterized.

After characterization, evaluate three paths:

### Path A — exact native reuse (preferred if reliable)

Feed our verified `PizzaModel` into the game and invoke/reuse the game's native image generator.

Advantages:

- highest visual fidelity;
- no renderer duplication;
- automatically uses real meshes/materials/shaders.

### Path B — native renderer with controlled deterministic capture

Reuse game objects/assets/rendering but provide a controlled camera/render target and explicit capture timing.

Useful if stock save JPEG is visually correct but nondeterministic or poorly sized.

### Path C — independent replica

Reimplement the whole rendering/image pipeline only if A/B are impossible.

This is the most expensive path and must not be chosen merely because it seems cleaner architecturally.

## 11. Possible improvements after proof

Only after the native path is understood, consider:

- deterministic seed/order where stock behavior is nondeterministic;
- higher internal render resolution followed by exact downsample;
- improved antialiasing;
- better JPEG quality while retaining native visual framing;
- PNG option for lossless internal evidence while keeping JPEG compatibility;
- collision-aware topping distribution;
- aesthetically balanced placement while preserving native coordinate contract;
- density masks per dough shape;
- edge avoidance and center-weight controls;
- ingredient-specific rotation rules;
- reproducible design seeds.

Any improvement must remain optional and must not break native Save/reload compatibility.

## 12. Deliverables

Claude should ultimately produce:

```text
docs/NATIVE_PIZZA_JPEG_ALGORITHM.md
research/jpeg-pipeline/callgraph.json
research/jpeg-pipeline/method-map.csv
research/jpeg-pipeline/experiment-results.csv
research/jpeg-pipeline/image-metrics.json
research/jpeg-pipeline/tool-versions.json
research/jpeg-pipeline/sample-models/
research/jpeg-pipeline/sample-jpegs/
research/jpeg-pipeline/diffs/
```

If the repository should not retain game-produced JPEGs, retain hashes/metrics and store the binary evidence under the configured evidence root instead; document the exact reference.

## 13. Completion criteria

This reverse-engineering track is complete only when we can answer, with retained evidence:

- what method/path generates the image;
- what 3D transforms feed it;
- what camera/render target creates it;
- how draw/layer ordering works;
- what post-processing/crop/scale is applied;
- what JPEG encoder/settings are used;
- whether output is deterministic;
- which model changes affect which image changes;
- whether native reuse is sufficient or an improved controlled capture is justified.

Until then, label the native JPEG algorithm **PARTIALLY CHARACTERIZED**, not complete.
