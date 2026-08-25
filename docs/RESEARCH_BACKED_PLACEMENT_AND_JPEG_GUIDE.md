# SCOPE: PC3 PIZZA CREATOR ONLY — Research-Backed Placement and JPEG Reverse-Engineering Guide

**Owner:** Claude — PC3 Pizza Creator  
**Repository:** `Ghenghis/Barros-Pizza-Creator`  
**Runtime profile:** `creator-0.11.272`  
**Purpose:** connect the Creator reverse-engineering program to established graphics, sampling, camera-calibration, and image-quality research so implementation choices are evidence-based rather than invented ad hoc.

This guide supplements:

- `docs/NATIVE_PIZZA_JPEG_REVERSE_ENGINEERING_ROADMAP.md`
- `docs/CURRENT_PIZZA_PLACEMENT_ALGORITHM_REFERENCE.md`
- `docs/CLAUDE_METHOD_FILE_IMPLEMENTATION_ATLAS.md`
- `contracts/jpeg-reverse-engineering.acceptance.json`

## 1. Core design rule

Use two explicit modes conceptually:

```text
NATIVE_MATCH
ENHANCED_DETERMINISTIC
```

`NATIVE_MATCH` must preserve or reuse the stock Creator rendering/image behavior once it is characterized.

`ENHANCED_DETERMINISTIC` may improve placement aesthetics and repeatability, but it must still emit a valid native `PizzaModel` and remain compatible with native Preview/Apply/Save/reload.

Do not improve an unknown stock algorithm and then mistake the improved behavior for the game's original behavior.

---

# 2. Research result: blue-noise / Poisson-disk sampling is the strongest baseline for natural topping separation

## Bridson 2007 — Fast Poisson Disk Sampling in Arbitrary Dimensions

Paper:

- Robert Bridson, *Fast Poisson Disk Sampling in Arbitrary Dimensions*, SIGGRAPH 2007 Sketches.
- DOI: `10.1145/1278780.1278807`
- Author PDF: `https://www.cs.ubc.ca/~rbridson/docs/bridson-siggraph07-poissondisk.pdf`

Why it matters here:

- Poisson-disk sampling enforces a minimum separation radius between samples.
- It produces blue-noise-like distributions without obvious regular grids.
- Bridson's method is simple and efficient enough for interactive generation.

### Pizza mapping

Use it for approximately round/symmetric topping footprints:

```text
pepperoni-like slices
meatballs
olive-like pieces
small vegetable chunks
```

For each ingredient size, infer or measure a footprint radius `r_i` from the real rendered mesh/image.

Reject a candidate point if it violates pairwise spacing.

For equal radius:

```text
||p_i - p_j|| >= r
```

For variable ingredient radii use a conservative pairwise rule such as:

```text
||p_i - p_j|| >= clearance * (r_i + r_j)
```

where `clearance` is calibrated from native overlap behavior, not guessed as a release fact.

### Recommended role

Poisson-disk should replace purely random radius selection in an optional enhanced mode when the goal is visually balanced non-clumping placement.

---

# 3. Research result: sample elimination is ideal when we know the desired piece count

## Yuksel 2015 — Sample Elimination for Generating Poisson Disk Sample Sets

Paper:

- Cem Yuksel, *Sample Elimination for Generating Poisson Disk Sample Sets*, Computer Graphics Forum 34(2), 2015.
- DOI: `10.1111/cgf.12538`
- Author PDF: `https://www.cemyuksel.com/research/sampleelimination/sampleelimination.pdf`

Important property:

The algorithm begins with an oversampled candidate set and greedily removes high-conflict samples until the desired count remains. The paper specifically emphasizes that the desired output size can be specified without manually choosing a Poisson radius first.

### Why this maps extremely well to pizza

The Creator recipe already gives us a requested piece count indirectly through grams and native per-piece amount.

So enhanced placement can do:

```text
1. determine exact desired piece count N
2. generate 3N–8N deterministic candidate positions inside the real dough mask
3. weight conflicts using ingredient footprint/edge/density rules
4. eliminate candidates until N remain
5. assign rotations
6. emit explicit native positions/rotations
```

This is likely a better fit than repeatedly guessing a radius until exactly N samples happen to fit.

---

# 4. Research result: capacity-constrained Voronoi methods give us density control without visible clumps

## Balzer, Schlömer, Deussen 2009

Paper:

- Michael Balzer, Thomas Schlömer, Oliver Deussen, *Capacity-Constrained Point Distributions: A Variant of Lloyd's Method*, ACM Transactions on Graphics 28(3), 2009.
- DOI: `10.1145/1531326.1531392`
- Project page: `https://graphics.uni-konstanz.de/publikationen/Balzer2009CapacityconstrainedPoint/index.html`

The method optimizes point sets toward blue-noise characteristics while adapting to a supplied density function. Equalized weighted Voronoi capacity avoids points becoming visually over-important simply because of local density.

## de Goes et al. 2012 — Blue Noise through Optimal Transport

Paper:

- Fernando de Goes, Katherine Breeden, Victor Ostromoukhov, Mathieu Desbrun, *Blue Noise through Optimal Transport*.
- PDF: `https://geometry.caltech.edu/pubs/dGBOD12.pdf`

The work formulates capacity-constrained Voronoi distribution through optimal transport and supports arbitrary density functions.

### Pizza mapping

Define a density field over the dough:

```text
rho(x,z) = base_density
           * shape_mask(x,z)
           * edge_margin(x,z)
           * requested_distribution(x,z)
           * ingredient_specific_bias(x,z)
```

Examples:

- `center`: high density toward center.
- `ring`: annular density band.
- `edge`: density peaks near a safe inner perimeter.
- `even`: near-uniform density.
- `artistic`: a deterministic multi-lobe field.

A capacity-constrained relaxation pass can then move initial samples toward the target density while reducing clumping.

### Recommended role

Do **not** use full optimal transport for every interactive pizza unless performance proves acceptable.

A practical hierarchy is:

```text
golden-angle or random candidate seed
    -> Poisson/sample-elimination separation
    -> 2–8 bounded Lloyd/capacity-style relaxation passes
    -> final shape/edge/collision validation
```

---

# 5. Research result: anisotropic blue noise is directly applicable to elongated toppings

## Li, Wei, Sander, Fu 2010 — Anisotropic Blue Noise Sampling

Paper:

- Hongwei Li, Li-Yi Wei, Pedro V. Sander, Chi-Wing Fu, *Anisotropic Blue Noise Sampling*, ACM Transactions on Graphics 29(6), 2010.
- DOI: `10.1145/1882261.1866189`
- Author/project page: `https://www.liyiwei.org/papers/noise-siga10/`

The paper extends dart throwing and relaxation to anisotropic samples and explicitly lists **object distribution** as an application.

## Wang, Hu, Urahama 2013 — Anisotropic Lp Poisson Disk Sampling for Adaptively Shaped Pieces

Paper:

- Tao Wang, Zhongying Hu, Kiichi Urahama, *Anisotropic Lp Poisson Disk Sampling for NPR Image with Adaptively Shaped Pieces*, IEICE Transactions on Information and Systems E96-D(6), 2013.
- DOI: `10.1587/transinf.E96.D.1406`

This work is especially relevant because it discusses spatial arrangement of differently shaped pieces using anisotropic Poisson-disk sampling.

### Pizza mapping

Round-radius collision tests are insufficient for:

```text
bacon strips
long peppers
onion strips
elongated meat/vegetable meshes
```

Represent each ingredient footprint by an oriented ellipse or convex 2D footprint in pizza-plane coordinates.

A simple anisotropic ellipse metric for one piece is:

```text
delta = candidate - placed
q = R(-theta) * delta
D^2 = (q.x / a)^2 + (q.z / b)^2
```

where:

- `theta` is topping orientation;
- `a` is half-length + margin;
- `b` is half-width + margin.

For pairs with different shapes/orientations, use either:

1. conservative combined ellipse/Minkowski bounds; or
2. exact 2D convex-footprint intersection once real footprint polygons are known.

### Orientation field ideas

Allow deterministic orientation policies:

```text
RANDOM_SEEDED
RADIAL
TANGENTIAL
ALTERNATING
FLOW_FIELD
NATIVE_MATCH
```

For a ring distribution, tangential orientation often looks intentional without forming a rigid grid:

```text
theta = atan2(z, x) + 90 degrees + seeded_jitter
```

For radial orientation:

```text
theta = atan2(z, x) + seeded_jitter
```

These are enhanced-mode options only until stock orientation behavior is characterized.

---

# 6. Research result: Poisson sampling can operate on actual surfaces rather than only a flat circle

## Bowers, Wang, Wei, Maletz 2010

Paper:

- John Bowers, Rui Wang, Li-Yi Wei, David Maletz, *Parallel Poisson Disk Sampling with Spectrum Analysis on Surfaces*, ACM Transactions on Graphics 29(6), 2010.
- DOI: `10.1145/1882261.1866188`
- Microsoft Research page: `https://www.microsoft.com/en-us/research/publication/parallel-poisson-disk-sampling-with-spectrum-analysis-on-surfaces/`

The method supports adaptive Poisson-disk sampling on arbitrary manifold surfaces.

## Li et al. 2008 — Dual Poisson-Disk Tiling

Paper:

- Hongwei Li, Kui-Yip Lo, Man-Kang Leung, Chi-Wing Fu, *Dual Poisson-Disk Tiling: An Efficient Method for Distributing Features on Arbitrary Surfaces*, IEEE TVCG 14(5), 2008.
- DOI: `10.1109/TVCG.2008.53`

The paper explicitly targets distribution of geometric features with a minimum separation guarantee to avoid overlap.

### Pizza mapping

If reverse engineering shows toppings are placed on a slightly non-planar dough mesh rather than a perfectly flat plane, we do not need to force a 2D approximation forever.

Enhanced placement can eventually:

```text
sample candidate point on dough surface
-> compute local tangent frame
-> perform spacing in tangent/geodesic approximation
-> orient topping to surface normal/tangent
-> convert final transform back to native world coordinates
```

Start in the existing X/Z plane because that matches the current native coordinate contract. Upgrade to mesh-surface sampling only if measured geometry warrants it.

---

# 7. Research result: the current golden-angle initializer is mathematically defensible

## Vogel 1979 — A Better Way to Construct the Sunflower Head

Paper:

- Helmut Vogel, *A Better Way to Construct the Sunflower Head*, Mathematical Biosciences 44(3–4), 1979.
- DOI: `10.1016/0025-5564(79)90080-4`

The current plugin already uses an angular step of approximately:

```text
2.399963229728653 radians ~= 137.5 degrees
```

which is the golden-angle/phyllotactic family of layouts.

### Keep it—but change its role

Golden-angle placement is excellent as a fast deterministic **initializer** because it spreads successive points around a disk without a simple repeating spoke pattern.

It is weaker than Poisson/anisotropic methods at respecting variable topping footprints and collision constraints.

Recommended enhanced pipeline:

```text
golden-angle seed
-> dough-mask projection
-> variable/anisotropic clearance
-> sample elimination or local repair
-> bounded Voronoi relaxation
```

This keeps the current deterministic strength while improving spatial quality.

---

# 8. Proposed enhanced placement algorithm v1

This is an optional improvement target after native characterization.

## Inputs

```text
shape_id
native dough/mesh boundary
recipe seed
ingredient ID
size
piece count
measured 2D footprint
requested distribution
orientation policy
edge margin
layer policy
```

## Stage A — build real dough domain

Preferred sources in order:

1. exact dough mesh projected into pizza plane;
2. native placement/dough geometry sufficient to derive a mask;
3. conservative shape polygon validated against runtime.

Do not use a generic circle for Star/Triangle/Square if a real native domain is available.

## Stage B — produce deterministic candidates

Use golden-angle/phyllotactic sequence plus small seeded jitter, or a deterministic candidate grid/random set.

Generate more candidates than needed:

```text
candidate_count = clamp(piece_count * oversample_factor, ...)
```

Suggested experimental oversample factors:

```text
3x
5x
8x
```

Measure quality/performance before selecting a default.

## Stage C — shape and edge rejection

Reject candidates outside the dough domain or violating the ingredient-specific edge margin.

For footprint `F_i(theta)` require:

```text
F_i translated to p_i lies entirely inside safe_dough_domain
```

where practical.

## Stage D — collision/separation

Use:

- isotropic radius for roughly circular toppings;
- oriented ellipse/convex footprint for elongated toppings.

Sample elimination is preferred when exact piece count must be retained.

## Stage E — density relaxation

Perform a small bounded number of capacity/Lloyd-style relaxation iterations using the requested density field.

After each move:

- clamp/project into safe dough domain;
- re-check collision constraints;
- preserve determinism.

## Stage F — rotation

Choose orientation using ingredient metadata + requested policy.

Use seeded jitter to avoid artificial repetition.

Do not change orientation after verifier approval.

## Stage G — native transforms

Emit explicit final:

```text
IngredientID
Size
Position x/y/z
Rotation x/y/z
```

The plugin should consume these exact transforms instead of regenerating different positions.

## Stage H — stable layer/depth order

The current implementation sets:

```text
Y = 1.0 + global_index * 0.01
```

Keep this as compatibility baseline until the overlap experiments reveal what stock rendering actually requires.

Enhanced layer ordering should eventually be based on measured native behavior and semantic layer classes, not arbitrary ingredient-list order.

---

# 9. Proposed objective function for automated aesthetic optimization

After footprint and native constraints are known, score a candidate layout with a weighted objective.

Conceptually minimize:

```text
E =
    w_overlap  * overlap_penalty
  + w_edge     * edge_violation_penalty
  + w_density  * density_error
  + w_cluster  * unintended_clustering
  + w_regular  * excessive_regular_pattern
  + w_orient   * orientation_conflict
  + w_native   * native_contract_violation
```

Hard constraints should never be traded away for aesthetics:

```text
valid native ingredient ID
valid native size
inside native safe domain
placement count
native coordinate bounds
serializable/reloadable transform
```

Use optimization only for the soft terms after hard constraints pass.

---

# 10. JPEG/render reverse engineering: official Unity 2017 clues

## ScreenCapture is PNG, not JPEG

Unity 2017.3 `ScreenCapture.CaptureScreenshot(filename, superSize)` captures a screenshot to a **PNG** file.

Therefore, if the stock Creator's saved pizza asset is truly a JPEG, a direct call to `ScreenCapture.CaptureScreenshot` cannot by itself be the final JPEG-writing operation.

This narrows static tracing priorities toward:

```text
Texture2D.ReadPixels
RenderTexture
Camera.targetTexture
Camera.Render
ImageConversion.EncodeToJPG
File.WriteAllBytes / FileStream
custom JPG encoder
```

## ReadPixels tells us what to trace

Unity 2017.3 `Texture2D.ReadPixels` copies pixels from the currently active RenderTexture/view into a readable texture.

If the stock pipeline uses it, capture:

```text
active RenderTexture identity
source rectangle
Texture2D width/height/format
frame timing
```

## EncodeToJPG hypothesis

Unity's `ImageConversion.EncodeToJPG` supports quality values 1–100 with default quality 75 when quality is omitted, and JPEG has no alpha channel.

This is a **hypothesis target**, not a claim that PC3 uses this API.

If the decompiled call is:

```text
ImageConversion.EncodeToJPG(tex)
```

then Unity's documented default quality becomes strong static evidence for quality 75; still validate the produced quantization tables against real stock JPEGs.

If the game passes an explicit quality parameter or uses another encoder, record the actual value/path instead.

---

# 11. Recover the hidden camera mathematically with a planar homography

## Zhang 2000 — camera calibration from a plane

Paper:

- Zhengyou Zhang, *A Flexible New Technique for Camera Calibration*, IEEE TPAMI 22(11), 2000.
- DOI: `10.1109/34.888718`
- Microsoft Research page: `https://www.microsoft.com/en-us/research/publication/a-flexible-new-technique-for-camera-calibration/`

The pizza top is close enough to a planar calibration surface that controlled topping locations can identify the world-to-image mapping.

## Experiment

Use one visually identifiable asymmetric ingredient piece at known coordinates.

Capture at least 6–12 distinct X/Z locations, covering center and edges.

For each:

```text
world = (X, Z)
image = measured topping centroid (u, v)
```

Fit both:

### Affine model

```text
u = aX + bZ + c
v = dX + eZ + f
```

### Projective homography

```text
[u v 1]^T ~ H [X Z 1]^T
```

Compare held-out residual error.

Interpretation:

- affine fit nearly as good as homography -> effectively orthographic/top-down or weak perspective;
- homography materially better -> perspective/projective capture;
- systematic residual distortion -> investigate camera lens/post-process/non-planarity/crop/resize.

Once `H` is known, we can predict where any native X/Z point should appear in the saved JPEG and distinguish placement errors from rendering/encoding errors.

---

# 12. Recover ingredient orientation from image measurements

For an asymmetric topping:

1. segment/difference the topping from a baseline image;
2. collect changed pixels;
3. compute centroid;
4. compute 2D covariance matrix of changed-pixel coordinates;
5. principal eigenvector gives dominant image orientation;
6. compare image orientation to native Y rotation.

Run rotations:

```text
0
30
45
60
90
120
135
180
270 degrees
```

Fit:

```text
image_angle ~= s * native_yaw + offset (mod 180 or 360 depending on topping symmetry)
```

This gives a measured rotation transfer function.

---

# 13. Determine draw/layer ordering

Use two high-contrast/asymmetric ingredient types at the same X/Z.

Controlled variables:

```text
list order
Y value
Y difference
rotation
ingredient material/type
```

Experiments:

```text
A then B, same Y
B then A, same Y
A then B, A lower Y
A then B, A higher Y
```

Observe which object wins the overlapping pixels.

This separates:

```text
model-list order
world depth
renderer sorting
material render queue/depth test
```

If RenderDoc is available, confirm the actual draw order and depth state from the captured frame.

---

# 14. JPEG forensic measurements

Do not compare JPEGs only by file size or visual appearance.

Parse JPEG markers and retain:

```text
SOI/EOI validity
SOF dimensions/components/sampling factors
DQT quantization tables
DHT Huffman tables if present
SOS scan structure
APP/COM metadata
progressive vs baseline
restart interval if present
```

Use `libjpeg-turbo` tools or a small parser for deterministic extraction.

Why DQT matters:

JPEG quality settings are realized through quantization tables. Two images with different scene pixels but the same encoder settings can still expose the same DQT/sampling structure.

This helps separate:

```text
render changes
from
encoder-setting changes
```

---

# 15. Image comparison metrics — research-backed stack

## Exact SHA-256

Use first.

```text
same hash -> byte-identical output
```

Different hash does not automatically mean meaningful visual difference.

## RMSE / MAE / PSNR

Useful for exact pixel-error magnitude and compression noise.

ImageMagick's `compare` supports mathematical metrics including RMSE, MAE, PSNR and SSIM/DSSIM in current ImageMagick 7.

## SSIM

Reference:

- Zhou Wang, Alan Bovik, Hamid Sheikh, Eero Simoncelli, *Image Quality Assessment: From Error Visibility to Structural Similarity*, IEEE TIP 13(4), 2004.
- DOI: `10.1109/TIP.2003.819861`

SSIM is useful because it measures structural similarity rather than only pointwise pixel error.

For reproducibility, either:

- use ImageMagick 7 SSIM with recorded version/settings; or
- use `skimage.metrics.structural_similarity` with explicit `data_range` and documented parameters.

For close adherence to the original Wang implementation, scikit-image documents:

```text
gaussian_weights = True
sigma = 1.5
use_sample_covariance = False
explicit data_range
```

## Difference bounding box

Compute the smallest rectangle containing all pixels whose absolute difference exceeds a controlled threshold.

This is extremely useful for rotation/position tests: if only the topping footprint changes, the diff should stay localized rather than affecting the entire image.

## Registration before comparison

Do **not** auto-register images for the first determinism test; a camera shift is itself evidence.

Registration/homography correction is a secondary analysis to determine whether differences are explained by framing alone.

---

# 16. Recommended reverse-engineering tools from current official sources

Record exact version and download hash in `research/jpeg-pipeline/tool-versions.json`.

## ILSpy

Official repository:

`https://github.com/icsharpcode/ILSpy`

Use for:

- whole-assembly text/method searches;
- decompilation;
- metadata/call relationships.

Use only official GitHub releases. The ILSpy project explicitly warns that it does not own `ilspy.org`.

## dnSpyEx + Unity Mono support

Official continuation/release family:

`https://github.com/dnSpyEx/dnSpy`

Unity Mono support:

`https://github.com/dnSpyEx/dnSpy-Unity-mono`

Use for:

- runtime breakpoints;
- call stacks;
- locals/argument values;
- tracepoints on image/save methods.

## AssetRipper

Official:

`https://github.com/AssetRipper/AssetRipper`

Current project documentation states support for Unity versions from 3.5.0 through modern releases, which includes the exact Creator Unity 2017.3 line.

Use for:

- camera/prefab/scene inspection;
- mesh/material/texture/shader inspection;
- identifying dedicated preview/thumbnail objects.

## RenderDoc

Official:

`https://github.com/baldurk/renderdoc`

Use only if frame capture works with the exact Creator graphics API/runtime.

Use for:

- draw-call order;
- D3D render targets;
- camera/output dimensions;
- meshes/textures/materials/shaders;
- depth/blend state;
- final blit/readback candidates.

## ImageMagick 7

Official:

`https://imagemagick.org/`

Use for:

- RMSE/MAE/PSNR/SSIM comparisons;
- visual diff images;
- identify/metadata inspection.

## libjpeg-turbo

Official:

`https://github.com/libjpeg-turbo/libjpeg-turbo`

Use for:

- JPEG header/quantization/subsampling inspection;
- decompression/reference tooling;
- controlled encoder comparisons when testing whether Unity resembles an IJG-style quality setting.

---

# 17. Research-informed experiment order

This order maximizes information per runtime save.

## Phase 1 — encoder determinism

```text
same exact model -> save 5 times
```

If byte-identical, great.

If not:

- compare DQT/SOF/metadata;
- decode and compare pixels;
- isolate metadata vs rendered-frame variation.

## Phase 2 — camera calibration

```text
single piece
known X/Z grid
constant rotation/size
```

Fit affine + homography.

## Phase 3 — orientation transfer

```text
single asymmetric piece
constant X/Z/size
rotation sweep
```

Fit native yaw -> image angle.

## Phase 4 — footprint/size

```text
single ingredient
Large/Medium/Small
same center/rotation
```

Infer safe footprint parameters.

## Phase 5 — depth/order

```text
two overlapping pieces
order/Y factorial test
```

## Phase 6 — count/density

```text
1, 2, 4, 8, 16, 32 pieces
```

Measure coverage, overlap, framing, and encoder behavior.

## Phase 7 — shape

```text
Round/Square/Star/Triangle
```

Measure camera framing and safe dough domain.

## Phase 8 — algorithm comparison

Generate matched recipe sets using:

```text
CURRENT_GOLDEN_ANGLE
POISSON_DISK
SAMPLE_ELIMINATION
ANISOTROPIC_POISSON
POISSON_PLUS_CVT
```

For each evaluate:

- native validity/reload;
- collision count;
- minimum pair spacing;
- edge violations;
- density uniformity;
- visual distribution spectrum where useful;
- runtime JPEG;
- deterministic repeatability.

Keep `NATIVE_MATCH` separate from enhanced alternatives.

---

# 18. Suggested final algorithm decision matrix

At the end of research, fill this with evidence rather than preference.

| Component | Native behavior | Current Barro's | Enhanced candidate | Decision |
|---|---|---|---|---|
| piece count | TBD | grams / native amount | same | TBD |
| seed | TBD | name/explicit seed | explicit deterministic seed | TBD |
| position | TBD | golden-angle + radius modes | sample elimination / anisotropic Poisson | TBD |
| shape boundary | TBD | round-like + square clamp | exact dough domain | TBD |
| orientation | TBD | seeded random Y | ingredient-aware anisotropic policy | TBD |
| overlap | TBD | no true footprint collision | footprint-aware clearance | TBD |
| layer order | TBD | global Y +0.01 | measured native-compatible stable layers | TBD |
| camera | TBD | native renderer | native reuse | TBD |
| JPEG encoder | TBD | native stock save | native reuse or controlled capture | TBD |

Final decisions must use one of:

```text
MATCH_NATIVE
KEEP_CURRENT
ENHANCED_OPTIONAL
REPLACE_WITH_PROVEN_BETTER
UNKNOWN
```

---

# 19. Bottom-line recommendation from the literature

For a future enhanced-but-native-compatible pizza generator, the strongest architecture is:

```text
real native dough domain
+ exact native ingredient footprints
+ deterministic golden-angle/candidate initialization
+ variable-radius / anisotropic Poisson separation
+ sample elimination to hit exact piece count
+ bounded capacity/CVT relaxation for requested density
+ ingredient-aware deterministic orientation
+ measured native-compatible Y/layer ordering
+ explicit position/rotation serialization
+ native PizzaModel
+ native renderer
+ native JPEG generator whenever possible
```

This is significantly more defensible than pure random placement or a handcrafted collection of special-case circles, while still allowing `NATIVE_MATCH` mode to reproduce the stock Creator behavior once reverse engineering is complete.
