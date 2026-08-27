# Barro's v1.2 live Windows proof — 2026-08-27

## Observed live result

The 1.2.0-rc1 artifact was installed into the real Steam Pizza Creator folder and loaded in the running 1920×1080 game. No unrelated game project was modified.

| Check | Result | Evidence |
|---|---|---|
| BepInEx loader | Pass | BepInEx 5.4.23.5 logged `Loading [Barro's AI Pizza Designer 1.2.0]`. |
| Sidecar startup and provider health | Pass | `http://127.0.0.1:48173/health` returned `ok=true`, `version=1.2.0-rc1`, `provider=openai-compatible`, and `online=true`. |
| Native tab clearance | Pass | Runtime event: `left=1346.0; right=1920.0; width=574.0; tab_right=1340.0; gap=6.0`. All five native tabs are visible in the retained image. |
| Inspiration toggle | Pass | The bottom control changed from `Ideas OFF` to `Ideas ON`; the status changed to `Local inspiration is on. Up to three indexed designs may guide the next request.` |
| Safe default | Pass | The toggle was returned to OFF after capture because no source images have been imported. |
| Inspiration endpoint | Pass, empty | `/inspiration` returned `configured=false`, `count=0`, `max_items=500`, and `total_bytes=0`. |
| Bulk Facebook/export import | Not run | No exact album/page/export folder and no reuse-rights classification were supplied. The importer is ready, but the repository and installed library contain zero source images. |
| Vision use of an imported image | Not run | There is no imported image to send. The backend never claims that an empty or offline-selected image was analyzed. |
| Microphone/STT | Blocked | Health truthfully reports `stt_configured=false`; the machine still has no working recording input for this game run. |

## Automated verification

`py -3 -m unittest discover -s tests -v`: **71 tests run, 71 passed, 0 failed**.

This includes all 87 ingredient profiles, curated pairing suggestions, cohesion scoring, validated image import and deduplication, the 500-item ceiling, maximum three images per request, offline truthfulness, HTTP capability reporting, packaging boundaries, and the prior game contracts.

## Certified artifact and visual proof

- Artifact: `artifacts/Barros.PizzaCreator.AI.dll`
- Artifact size: 71,168 bytes
- Artifact SHA-256: `e29f62d202ce4fb4037945da0b490e46dc4c657dabc42a65fcbcf6dfce2483ae`
- Visual: `docs/evidence/live-v12-inspiration-toggle-2026-08-27.jpg`
- Visual size: 250,160 bytes
- Visual SHA-256: `56d7876d87465c6f10ab832b599e2a24470ad45e82f879711d672bec734cdebd`

## Certification boundary

This run certifies the v1.2 binary loading in the real game, the fitted UI, the Inspiration Library toggle, and the healthy empty-library backend. It does not certify downloading or visually analyzing Facebook images; those require the user's exact authorized source or exported folder.
