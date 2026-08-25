# SCOPE: PC3 PIZZA CREATOR ONLY — JPEG Reverse-Engineering Tooling Setup

**Owner:** Claude — PC3 Pizza Creator  
**Runtime target:** `creator-0.11.272`  
**Purpose:** stage a reproducible Windows research toolbox from official sources and retain tool identities/hashes with the experiment evidence.

Do not install tools into the game `Managed`, `BepInEx`, `StreamingAssets`, or `BarrosAI` runtime trees. Keep research tooling in a separate labeled folder such as:

```text
S:\Unity_Games\PC3 - Pizza Creator\_research-tools
```

If that drive/path is unavailable, use a separate local research-tools directory and record the resolved path.

## Pinned core tools — verified official release metadata as of 2026-08-25

### ILSpy 10.1.1

Official project: `https://github.com/icsharpcode/ILSpy`

Preferred self-contained Windows x64 archive:

```text
ILSpy_selfcontained_10.1.1.8388-x64.zip
https://github.com/icsharpcode/ILSpy/releases/download/v10.1.1/ILSpy_selfcontained_10.1.1.8388-x64.zip
SHA-256 e2e733760f10e215aa705fba393601a1c7c6536cccda594bda56f45a4c42e2ae
```

The self-contained build avoids making .NET 10 availability a prerequisite for static research.

**Security note:** the ILSpy project explicitly warns that it does not own `ilspy.org`; use GitHub Releases only.

### dnSpyEx 6.6.0

Official continuation: `https://github.com/dnSpyEx/dnSpy`

Preferred Windows x64 archive:

```text
dnSpy-net-win64.zip
https://github.com/dnSpyEx/dnSpy/releases/download/v6.6.0/dnSpy-net-win64.zip
SHA-256 8ed48f165dc355e869f3a0037ad4f9216147f995a5ae0258b296eeef1f73aab0
```

Unity Mono support project:

```text
https://github.com/dnSpyEx/dnSpy-Unity-mono
```

Use dnSpyEx for breakpoints, tracepoints, call stacks, arguments and locals around native Save/image-generation methods.

### AssetRipper 2.0.0

Official project: `https://github.com/AssetRipper/AssetRipper`

Released 2026-08-24. Preferred Windows x64 archive:

```text
AssetRipper_win_x64.zip
https://github.com/AssetRipper/AssetRipper/releases/download/2.0.0/AssetRipper_win_x64.zip
SHA-256 9a7ef0e7c5c3ea5b90b4e6d855e2d98d5f7ec8c3f9e26fccbc194c6a7b01baf7
```

Use it to inspect camera objects, preview/thumbnail prefabs, render textures, meshes, materials, shaders and textures in the exact Unity 2017.3 build.

### libjpeg-turbo 3.2.0

Official project: `https://github.com/libjpeg-turbo/libjpeg-turbo`

Preferred Windows Visual C++ x64 installer:

```text
libjpeg-turbo-3.2.0-vc-x64.exe
https://github.com/libjpeg-turbo/libjpeg-turbo/releases/download/3.2.0/libjpeg-turbo-3.2.0-vc-x64.exe
SHA-256 662761d8ba8dae04aec74023ebaeceb856c2b56b9b59cfd180759d26300dda42
```

Use its JPEG utilities/reference decoder to inspect/compare JPEG structure and to test whether native quantization/subsampling resembles common IJG/libjpeg quality configurations.

## Graphics debugger — RenderDoc 1.45

Official project: `https://github.com/baldurk/renderdoc`

Current stable release identified from the official release metadata:

```text
RenderDoc 1.45
released 2026-07-02
```

RenderDoc's GitHub release points Windows users to the official binary build service at `https://renderdoc.org/builds` rather than attaching the Windows binaries to GitHub.

On Windows with `winget`, current package identity is:

```text
BaldurKarlsson.RenderDoc
```

Recommended pinned install command when an agent/operator intentionally chooses to install it:

```text
winget install --id BaldurKarlsson.RenderDoc --exact --version 1.45.0 --accept-package-agreements --accept-source-agreements
```

Do not make RenderDoc mandatory for the first static pass. Use it if static/dnSpy tracing does not fully expose camera/render-target/draw-order state.

## Image analysis — ImageMagick 7

Official downloads: `https://imagemagick.org/download/`

The official ImageMagick site currently offers Windows 7.1.2-29 builds and documents official winget aliases such as:

```text
winget install ImageMagick.Q16-HDRI
```

Because ImageMagick release versions advance frequently, do **not** hard-code an old ImageMagick URL into the Creator research contract. At experiment time:

1. install from the official site/official winget package;
2. record `magick -version`;
3. hash the installed executable or downloaded installer if retained;
4. write version/hash into `research/jpeg-pipeline/tool-versions.json`.

## Python analysis environment

Keep Python image-analysis dependencies isolated in a venv rather than changing the Creator runtime Python installation.

Recommended packages:

```text
Pillow
numpy
scikit-image
```

The repository analyzer `scripts/analyze_jpeg_experiment.py` works without these for raw JPEG structure/hash analysis, then automatically adds decoded pixel metrics and Wang-compatible SSIM when these packages are available.

Record:

```text
python --version
pip freeze
```

with the research evidence.

## Minimum tool use by research gate

| Gate area | Minimum | Escalation |
|---|---|---|
| static save/image call graph | ILSpy | dnSpyEx tracepoints |
| runtime call stack/arguments | dnSpyEx | BepInEx instrumentation |
| camera/prefab/material inventory | AssetRipper | RenderDoc |
| draw order/depth/render target | source/dnSpy if conclusive | RenderDoc |
| JPEG marker/quantization analysis | repository analyzer | libjpeg-turbo |
| pixel metrics/diffs | Pillow/scikit-image | ImageMagick |
| camera mapping | Python/numpy/scikit-image | OpenCV optional only if needed |

## Tool provenance file

For every research session write/update a non-secret evidence file conceptually shaped as:

```json
{
  "tools": [
    {
      "name": "ILSpy",
      "version": "10.1.1",
      "source": "official GitHub release",
      "download_sha256": "...",
      "executable_sha256": "..."
    }
  ]
}
```

A tool being installed is not a research PASS; it only establishes reproducibility.

## Do not do this

- Do not download ILSpy from `ilspy.org`.
- Do not use arbitrary dnSpy forks when the official dnSpyEx continuation is available.
- Do not replace game assemblies just to observe a call stack.
- Do not copy extracted proprietary assets into public releases.
- Do not mix research tooling into Studio/Workbench implementation directories.
- Do not expose credentials in tool/version evidence.
