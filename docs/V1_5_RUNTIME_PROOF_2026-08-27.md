# Barro's Pizza Creator 1.5 final proof — 2026-08-27

Version `1.5.0` was compiled against, installed into and launched from the real Steam **Pizza Connection 3 - Pizza Creator 0.11.272** folder on Windows 11. The original game assemblies and unrelated PC2, PC3, Unity, Claude and gateway projects were not modified.

## Exact build and automated proof

| Check | Result |
|---|---|
| Automated suite | **PASS — 107/107** tests |
| Plugin compilation | **PASS** — Windows .NET Framework compiler against the exact supplied Creator/Unity assemblies |
| Plugin artifact | `Barros.PizzaCreator.AI.dll`, 144,384 bytes |
| Plugin SHA-256 | `9514F6B339DDBF52001263E6922ADFC51758AAF388F448F7372366F3826DB5B3` |
| Installation mode | `certified-prebuilt` through the target-scoped installer |
| Target assembly SHA-256 | `EBF8698DF7CB4AF904C98C299994705EA529EFBDF1E8CCB3E7CA8CB42A1CBC1C` |
| Target firstpass SHA-256 | `F9CBF0951FC4D4B0788C47BBE41A3820FA333D293175BBB7CB398EB4728FD284` |

The final suite covers nested album discovery, recursive owner inboxes, protected internal folders, duplicate-safe relative track keys, playlist-v2 wiring, speech-rate SSML, no-overlap roundtable wiring, microphone controls and all existing Creator, art, attachment, ecosystem and truth-contract behavior.

## Live Windows observations

| Area | Result | Retained evidence |
|---|---|---|
| Loader and sidecar | **PASS** | BepInEx loaded `Barro's AI Pizza Designer 1.5.0`; `/health` returned `ok=true`, `version=1.5.0`, provider `openai-compatible`, `online=true`. |
| Five-tab geometry | **PASS** | Chat, AI Lab, Crew, Voice and Media were all visible and individually responsive; runtime event retained `left=1346`, `tab_right=1340`, `gap=6`. |
| Large music library UI | **PASS** | Named playlist controls, search, filter, sort, bulk Add/Remove and the dedicated scroll area rendered without covering the five native tabs. See `docs/evidence/live-v15-media-library-2026-08-27.png`. |
| Live music search | **PASS** | Entering `Christmas` changed the library from `5 shown · 5 total` to `1 shown · 5 total` and retained only `Twelve Slices of Christmas`. See `docs/evidence/live-v15-media-search-2026-08-27.png`. |
| Music playback | **PASS** | Barro's exclusive mode remained active, stock music remained off, a real waveform moved, and the second queued OGG played. Health reported five tracks and the 48 kHz stereo / Vorbis q8 / -14 LUFS / -1 dBTP profile. |
| Four-agent text interaction | **PASS** | A real Crew request returned separate Flavor Chef, Cost Manager, Customer Scout and Creative Director cards plus a 68% `Desert Fire` consensus. See `docs/evidence/live-v15-crew-response-2026-08-27.png`. |
| Sequential voice runtime | **READY, NOT AUDIBLY RUN** | The compiled queue holds one music-focus window and advances turns only after each clip finishes. Azure Speech is disabled on this PC, so no audible pass is claimed. |
| Microphone readiness | **READY, HARDWARE BLOCKED** | Device selector, Refresh, Live/Mute, input gain and meter rendered correctly. Windows exposed no microphone, so capture/transcription was not run. See `docs/evidence/live-v15-microphone-ready-2026-08-27.png`. |
| Runtime log | **PASS** | The final loader log showed 1.5.0 initialization, bridge injection, tab/header fitting and media playback with no relevant exception or traceback. |

## Truth boundary

Named-playlist persistence and nested folders are compiled and automated-test green; the visible final library and live search are Windows-observed. No playlist was deleted and no owner song was removed during proof. Audible Azure voices and real microphone capture remain pending until their external prerequisites exist. The game was left running on the final v1.5 installation.
