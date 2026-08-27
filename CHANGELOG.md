# Changelog

## 1.5.0 — 2026-08-27

- Rebuilt the Media Deck for large owner libraries: nested album folders, duplicate-safe relative track IDs, a dedicated scroll area, search, queue/audio/video filters, A–Z/newest/folder/queue sorting and bulk add/remove.
- Added multiple named playlists with create, duplicate, rename, protected removal, previous/next selection and automatic migration from the v1 single startup queue.
- Made the import inbox recursive so owner-created album folders remain organized after lossless source intake and normalized 48 kHz OGG conversion.
- Added a sequential agent roundtable. Crew turns enter one queue, never overlap or cut each other off, and hold one music-focus window until the final voice finishes.
- Added agent voice volume, 0.9–1.1× speech rate and inter-speaker gap controls while retaining the balanced 24-voice English Azure roster and muted-by-default privacy boundary.
- Added Windows microphone device selection, refresh, mute, input gain and a real live input meter. Hardware capture still requires the user to connect and select a working microphone.
- Preserved Stock/Barro's one-source audio exclusivity, rounded panel styling, exact Creator 0.11.272 ABI lock and non-destructive game boundaries.

## 1.2.0-rc1 — 2026-08-27

- Added ingredient intelligence for all 87 exact game ingredients: readable names, compact flavor profiles, dietary tags, allergen flags and curated pairing strengths.
- Improved offline and online recipe composition so explicitly requested ingredients attract coherent complements instead of relying only on a fixed theme list.
- Added pairing cohesion to backend taste/popularity estimates while keeping the game's native scoring authoritative after preview/apply.
- Added a local-only Inspiration Library for up to 500 validated JPG, PNG or WebP pizza designs with SHA-256 deduplication and bounded three-image selection per AI request.
- Added an in-game `Ideas ON/OFF` control. Library images are sent only when the user enables it for a request.
- Added a Windows folder-picker importer and excluded the private inspiration image directory from Git and release ZIPs.
- Preserved the native-tab clearance repair verified at 1920×1080 in the real Steam game.

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
