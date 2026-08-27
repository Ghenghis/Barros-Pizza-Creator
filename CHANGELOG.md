# Changelog

## 1.2.0-rc2 — 2026-08-27

- Reconciled the mod against the exact private decompilation of Creator `Assembly-CSharp` and `Assembly-CSharp-firstpass`.
- Closed the native JPG pipeline: stock `ScreenCapture` renders 2560×1440, scales to 1280×720, encodes at quality 90, and writes directly under `StreamingAssets/Screenshots`.
- Rejected the former hidden-JPG-recipe hypothesis; editable pizza state is native recipe JSON under `Application.persistentDataPath/UserData/Recipes`.
- Added an **Export stock JPG** action that reuses the scene-local stock `ScreenshotButton`/`ScreenCapture`, preserves its screenshot-only UI transition, restores prior state, and verifies complete JPEG SOI/EOI bytes.
- Strengthened recipe save so success requires both the native recipe-list entry and a non-empty persisted JSON file.
- Changed F9 into an automated persisted-disk round trip through PC3's `ISerializerService`, catalog rebind, native load, and full signature verification instead of requiring a manual recipe-book reload.
- Added a fail-closed artifact-provenance guard: source-candidate packages omit the stale prior DLL and the Windows installer compiles against the exact installed Creator assemblies.
- Fixed literal `placements[*]` family matching in the controlled-stimulus verifier.
- Added a machine-readable native JPG/recipe contract pinned to the exact private source commit and blob hashes.

## 1.1.0-rc1 — 2026-08-25

- Hardened visual attachments with decoded magic-byte parsing for PNG, JPEG and WebP instead of trusting file extensions.
- Added bounded visual input limits, decoded dimension validation, SHA-256 metadata, MIME mismatch rejection and `/inspect-attachment`.
- Added the shared `pc3-image-handoff` schema with build-profile routing and the shared dual-build compatibility matrix.
- Added explicit separation between the Creator `0.11.272 / Unity 2017.3.1p4` runtime and Studio `1.11.403 / Unity 2017.4.40f1` runtime.
- Added the v2.2 ecosystem completion contract covering Workbench, Studio, exact image handoff, agents, recovery, publication and attachment-parser proof.
- Added Workbench/Studio ecosystem architecture and recovery diagrams plus safe GitLab mirroring helpers.
- Added one-command three-repository ecosystem audit/recovery evidence generation.
- Extended public CI with deterministic release ZIP reconstruction/verification and operator recovery-tool syntax checks.

## 1.0.0-rc1 — 2026-08-24

- Added the compact `BARRO'S PIZZA CREATOR` in-game header asset and runtime aspect-fit behavior for the stock Bakehouse title strip.
- Added a non-destructive fifth Pizza Creator tab with Chat, AI Lab, Design Crew and Chef Voice modes.
- Added live runtime catalog extraction and exact ID/size repair for all 87 supplied ingredients.
- Added real `PizzaModel` binding, 3D placement, preview/restore, apply and recipe-book save.
- Added game-native taste, popularity, cost and profit scoring plus deterministic novelty/originality.
- Added offline designer, OpenAI-compatible/LM Studio, Ollama and Anthropic provider routing.
- Added multimodal image and text attachments, microphone WAV capture, STT and conversation history.
- Added pinned dependency verification, source compilation, provider configuration, diagnostics and uninstall.

### Proof hardening — 2026-08-25

- Added the 24-gate layered proof contract, PowerShell runner, retained JSON/Markdown evidence, and explicit `not_run`/`blocked` states.
- Compiled and shipped a certified 66,560-byte plugin against the exact supplied PC3/Unity assemblies with full build provenance.
- Updated the installer to verify both game assembly hashes and use the certified DLL without requiring Visual Studio.
- Added structured runtime events for loader/UI geometry, Preview, Restore, Apply, Save, reload verification, microphone capture, and STT.
- Added F8 canonical mode screenshots, F9 saved/reloaded model verification, objective right-panel visual comparison, and difference images.
- Added GitHub Actions and GitLab CI checks plus an upstream primary-source compatibility audit.
- Expanded the automated suite from 14 to 20 passing tests, including the STT multipart request and educational/audio-pipeline contracts.
- Added a complete engineering/reverse-engineering reproduction notebook and a factual 24-gate status snapshot.
- Added a one-click, hash-manifested, decode-validated `Barros_Music` to Ogg Vorbis conversion pipeline without bundling placeholder audio.
- Added a deterministic release builder that regenerates manifests and verifies ZIP membership, hashes and CRCs.
