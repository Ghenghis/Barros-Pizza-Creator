# SCOPE: PC3 PIZZA CREATOR ONLY — JPEG Encoder Forensics Guide

**Owner:** Claude — PC3 Pizza Creator  
**Runtime profile:** `creator-0.11.272`  
**Purpose:** identify and characterize the stock Creator pizza-image JPEG encoder using file structure plus static/runtime evidence, without confusing a fingerprint match with proof of implementation identity.

## 1. Why JPEG structure matters

Two saved pizzas can have completely different pixel content while still being produced by the same encoder configuration. The JPEG container exposes stable structural evidence including:

- quantization tables (DQT);
- frame mode/dimensions/component sampling (SOF);
- Huffman table definitions (DHT);
- restart intervals (DRI);
- APP/COM marker payloads;
- progressive vs baseline scan structure.

These fields can remain stable while compressed scan data changes with the pizza.

## 2. Research basis

### Kornblum 2008

Jesse D. Kornblum, *Using JPEG Quantization Tables to Identify Imagery Processed by Software*, Digital Investigation 5 Supplement, 2008, DOI `10.1016/j.diin.2008.05.004`.

The work demonstrates that JPEG quantization tables can be used as evidence for distinguishing image-processing software/source families.

Creator use:

- fingerprint stock pizza JPEGs across many different recipes;
- determine whether DQT fingerprints remain invariant;
- compare native stock images to controlled test encoders only as a hypothesis aid.

### Cogranne 2018

Rémi Cogranne, *Determining JPEG Image Standard Quality Factor from the Quantization Tables*, arXiv:1802.00992.

The paper describes exact determination of a JPEG standard/IJG-family quality factor from quantization tables when those tables belong to the standard scaled family.

Creator use:

- if stock DQT exactly equals an IJG standard quality table pair, record the exact matching quality candidate;
- do **not** infer encoder identity from that match alone.

### 2026 JPEG-forensics survey

*A survey on JPEG image forensics: Exploring key advances and persistent challenges in compression and quantization analysis*, Computers & Security 165 (June 2026), 104864, DOI `10.1016/j.cose.2026.104864`.

The survey organizes current JPEG forensics around compression detection, quantization-step estimation, and applications of JPEG features. This supports treating DQT/quantization analysis as a current evidence technique rather than merely historical metadata inspection.

## 3. Executable repository tool

Use:

```text
scripts/fingerprint_jpeg_encoder.py
```

It imports the raw parser in:

```text
scripts/analyze_jpeg_experiment.py
```

and emits:

```text
jpeg-encoder-fingerprint.json
```

The fingerprint contains:

- complete parsed JPEG marker structure;
- DQT-only hash;
- DHT-only hash;
- combined encoder-structure hash;
- exact standard IJG quality-family matches for table 0/table 1 when applicable.

## 4. Correct inference ladder

Use this order and stop at the strongest evidence actually obtained.

### Level 0 — same/different bytes

```text
SHA-256 equal
```

means exact file identity only.

### Level 1 — same decoded pixels

Different bytes but identical decoded pixels can indicate metadata/encoder-stream differences without a visual change.

### Level 2 — same JPEG structural fingerprint

Same:

```text
DQT
DHT
SOF sampling/frame mode
APP/COM structure
DRI
scan structure
```

across many recipes strongly supports a stable encoder configuration.

It still does not identify the implementation.

### Level 3 — exact standard quality-family match

If DQT matches an IJG quality family exactly, record:

```text
standard_family = IJG-style scaled tables
quality_candidate = Q
```

Do not write:

```text
encoder = libjpeg
```

unless source/runtime evidence shows that implementation.

### Level 4 — static source identity

Decompiler evidence identifies the exact JPEG API/method invoked.

Examples of possible outcomes:

```text
ImageConversion.EncodeToJPG(texture, Q)
ImageConversion.EncodeToJPG(texture)
custom encoder method
third-party JPEG library
```

### Level 5 — runtime identity

Live breakpoints/tracepoints show the actual method is invoked during native pizza save/image generation with concrete arguments.

Only at this level should the implementation/path be described as runtime-proven.

## 5. Native JPEG fingerprint experiment

Collect at least:

```text
5 identical-model repeated saves
10 visibly different pizzas
4 dough shapes
3 ingredient sizes
rotation/position experiment outputs
post-native-reload re-save images
```

For every file retain:

```text
PizzaModel signature
JPEG SHA-256
encoder-structure SHA-256
DQT-only SHA-256
DHT-only SHA-256
SOF/sampling
APP/COM fingerprints
standard quality candidate(s)
```

Then group images by structural fingerprint.

### Expected interpretations

#### One fingerprint across everything

Likely one stable encoder configuration.

#### DQT stable, APP markers vary

Likely same compression settings with variable metadata.

#### DQT varies by image content

Investigate adaptive/custom encoder behavior or multiple save paths.

#### Dimensions/sampling vary by dough shape

Investigate shape-specific crop/resize/render-target behavior.

#### Identical model after native reload gets a different fingerprint

This points to changing encoder configuration/path, not merely scene/pixel nondeterminism.

## 6. Unity hypothesis testing

Unity 2017.3 documentation gives two useful boundaries:

- `ScreenCapture.CaptureScreenshot` writes PNG, so it cannot by itself be the final JPEG output path if the native recipe image is genuinely JPEG.
- `ImageConversion.EncodeToJPG` accepts a quality setting from 1–100 and documents default quality 75 when quality is omitted.

Therefore static tracing should actively test for:

```text
ImageConversion.EncodeToJPG(texture)
```

or:

```text
ImageConversion.EncodeToJPG(texture, explicitQuality)
```

If the no-quality overload is proven in the exact source/runtime and DQT also matches standard quality 75, those are mutually reinforcing lines of evidence.

If the DQT does not match standard quality 75, then one or more assumptions are wrong: a different overload, different encoder/table family, post-processing, or a non-Unity encoder may be involved.

## 7. Huffman tables as an additional fingerprint

Do not discard DHT because most quality discussions focus on DQT.

A stable DHT hash across native images can further distinguish a fixed encoder configuration. If DQT matches another encoder family but DHT does not, avoid a premature implementation-identification claim.

## 8. Sampling factors

Record component sampling from SOF, for example conceptually:

```text
4:4:4
4:2:2
4:2:0
```

The repository parser records horizontal/vertical sampling for every component rather than reducing it to a potentially ambiguous label.

This can reveal whether a hypothetical recreated encoder is structurally compatible with stock PC3 output.

## 9. APP markers and metadata

Record marker number, length, prefix and payload hash.

Useful possibilities include:

```text
JFIF APP0
Exif APP1
Adobe APP14
custom software/application marker
COM strings
```

Do not expose personal paths or secrets if any custom metadata unexpectedly contains them; sanitize the handoff while retaining a cryptographic fingerprint of the original evidence where appropriate.

## 10. Final encoder characterization table

Fill only from evidence:

| Component | State | Value/evidence |
|---|---|---|
| final JPEG method/API | UNKNOWN | static/runtime trace required |
| quality argument | UNKNOWN | source/runtime + DQT |
| DQT fingerprint | NOT_RUN | native samples required |
| IJG quality-family match | NOT_RUN | native samples required |
| DHT fingerprint | NOT_RUN | native samples required |
| chroma sampling | NOT_RUN | native samples required |
| frame mode | NOT_RUN | native samples required |
| APP/COM metadata | NOT_RUN | native samples required |
| output dimensions | NOT_RUN | native samples required |
| encoder deterministic config | NOT_RUN | repeated/different-image corpus required |

## 11. Truth rule

A matching quantization table is a **forensic fingerprint**, not implementation proof. The final `docs/NATIVE_PIZZA_JPEG_ALGORITHM.md` must separately state:

```text
FILE-STRUCTURE EVIDENCE
STATIC SOURCE EVIDENCE
LIVE RUNTIME EVIDENCE
```

and only claim the actual encoder implementation when the latter evidence supports it.
