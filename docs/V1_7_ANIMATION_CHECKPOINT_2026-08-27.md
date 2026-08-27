# Barro's v1.7 animation-lab checkpoint

Date: 2026-08-27 UTC

Branch: `codex/barros-v1.7-animation-lab`

Stable release boundary: v1.6 remains the packaged release; this is the next isolated development checkpoint.

## Outcome

The first Unity 2021-authored animation has been exported and rendered safely in the exact Unity 2017.3.1p4 Pizza Creator game. It is the small green provider-ready pulse in the connection badge.

## Export contract

- Asset: `assets/ui/generated/connection-pulse.png`
- PNG dimensions: 256×32
- Layout: eight 32×32 frames in a horizontal strip
- Playback: 8 fps
- PNG SHA-256: `13b30cb513f9d20780150a706002049d58dc8a2b58e629613a4e31e5f6b70510`
- Theme schema: 2, neutral PNG + JSON
- Runtime guard: normal 5 MiB/16..512 px texture boundary
- Fallback: the previous static green or amber dot remains when the strip is absent or rejected

## Retained proof

- Unity authoring log: `BARROS_UI_EXPORT_OK ... files=6 format=png+json`
- Exact game: Unity `2017.3.1.8332599`
- Plug-in load: `Barro's AI Pizza Designer 1.6.0` (v1.7 branch code keeps the stable package version until release promotion)
- Runtime marker: `ui.exported_animation_loaded detail=name=connection-pulse;frames=8;fps=8;target=Unity2017`
- Geometry marker: `left=1346; right=1920; tab_right=1340; gap=6`
- Certified development DLL SHA-256: `0284d7d480655d407e1d64efd86ff9e6d241786c440f24ab02291e6d532a9bbf`
- Automated suite: **116 passed**
- Screenshot: `docs/images/v17-live-connection-pulse-proof.jpg`

## Truth boundary

This proves a bounded PNG sprite-strip animation in the exact game. It does not prove that Unity 2021 animation clips, prefabs, scenes or AssetBundles can load in Unity 2017. They remain rejected by the compatibility design. The next distinct research step is an isolated Unity 2017.3.1p4 staging project for a harmless, separately hashed test bundle.

![Live connection-pulse checkpoint](images/v17-live-connection-pulse-proof.jpg)
