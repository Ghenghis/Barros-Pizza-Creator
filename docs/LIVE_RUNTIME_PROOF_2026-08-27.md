# Live Windows runtime proof — 2026-08-27

## Scope and safety boundary

The repaired build was installed and exercised only in this isolated working copy:

`work/game-copy/Pizza Connection 3 - Pizza Creator`

The Steam installation and unrelated PC2/PC3 projects were not modified. Native Save/reload was not exercised because the game may store it in shared Windows user-profile data outside the isolated folder.

## Observed result matrix

| Feature | Result | Retained proof |
|---|---|---|
| Loader and native fifth tab | Pass | BepInEx loaded; final tab event reports `x=70.0; y=-285.0; width=70.0; height=70.0; sibling=5`. |
| Fitted Barro's header | Pass | Final header event reports `banner_width=547.0; safe_width=547.0; close_reserve=78`. |
| Rounded parchment UI | Pass | Separate Chat, Lab, Crew, and Voice screenshots retained at 1920×1080. |
| MiniMax-compatible Chat | Pass | `Sonoran Sunset`, one valid recipe, no warning; visible in retained History. |
| AI Lab | Pass | Three game-valid recipes returned by a later live request with no warning. |
| Design Crew | Pass with fallback | Four agents completed and reached 52% consensus. The online draft failed JSON validation, so the deterministic built-in designer supplied the game-valid recipe. |
| Preview | Pass | `2026-08-27T10:44:13.3096539Z action.preview.success id=Desert Chorizo Classic; placements=12; dough=20; profit_factor=0.600`. |
| Start Over / restore | Pass | `2026-08-27T10:44:46.9915681Z action.restore.success Captured pre-preview PizzaModel reloaded.` |
| Apply | Pass | `2026-08-27T10:45:57.146372Z action.apply.success id=Sonoran Sunset; placements=9; dough=20; profit_factor=0.600`. |
| Topping spread | Pass | The native apply screenshot shows different ingredient families spread around the pizza; the placement contract test locks the pizza-wide golden-angle index. |
| History | Pass | Live history retained successful Chat, Lab, and Crew entries. |
| Attachment parsing | Automated pass | PNG/JPEG metadata, MIME-spoof rejection, invalid base64, and metadata-only HTTP output are covered. The native file chooser is not live-certified by this run. |
| Native Save/reload | Not run | Deliberately avoided to protect shared user-profile data. |
| Microphone capture | Blocked | `waveInGetNumDevs()` returned `0`; runtime recorded `voice.capture.failed`. |
| Speech-to-text | Blocked | Health reports `stt_configured=false`, `dedicated_endpoint_configured=false`, and `reachability=not_probed`; `/transcribe` refuses to pretend the text-only gateway supports audio. |

## Final automated verification

Command: `py -3 -m unittest discover -s tests -v`

Result: **65 tests run, 65 passed, 0 failed** on Windows 11.

This covers the backend, Chat/Voice HTTP contract, provider token-file resolution, catalog validity, attachment handling, proof contracts, exact placement-spread source guard, health capability truthfulness, and release/provenance agreement.

## Certified artifact

- Artifact: `artifacts/Barros.PizzaCreator.AI.dll`
- Size: 69,632 bytes
- SHA-256: `7489026cbac205b5ec501806d0820992c516deb08a9070db8d5d97bec9b8bf6a`
- Source tree SHA-256: `cc8b671d5a127eb0187c9bcb52a013a07a8085ee317843c03827240762c743d4`
- Compiler: Microsoft Visual C# Compiler 4.8.9032.0
- Target: Pizza Creator 0.11.272 / Unity 2017.3.1p4 x64 / BepInEx 5.4.23.5

Unity 2021.3.45f2 is used for the separate Unity MCP workbench, not to replace the shipped game's Unity runtime.

## Retained visual evidence

| File | SHA-256 |
|---|---|
| `docs/evidence/live-barros-tab-2026-08-27.png` | `78e766544f212fbbc6f4b85b44c736b3fbce197ed401581bebee3ed150431e936` |
| `docs/evidence/live-chat-rounded-2026-08-27.png` | `083db789344476564cbbc68677a6f6377cf07290ff63fd9b9d8b9730759b76dc` |
| `docs/evidence/live-lab-rounded-2026-08-27.png` | `b1e2bedcf62ba63eb5283142e870ef3cf14d2e1c39cd494b3c6ebff1f8756542` |
| `docs/evidence/live-crew-rounded-2026-08-27.png` | `5ecc9427a7334dd8019e79b2a8de0707d1757ebdb527f2fe1f53e503a2c3cd0f` |
| `docs/evidence/live-voice-blocked-2026-08-27.png` | `8dd685a6976daf8001cebacba2ae378c2d888e4ca9eb5f6a32e6cc594a46990e` |
| `docs/evidence/live-native-apply-sonoran-sunset-2026-08-27.png` | `845e96e6276043443032e494d7c6445749ce8f1d45b2ba040fd4c8840f108b83` |

## What is still needed for a full green Voice/Save claim

1. Enable or connect a Windows recording device.
2. Configure a dedicated speech-to-text endpoint in `BarrosAI/settings.json`, then run an actual capture/transcription test.
3. If the user authorizes writes to shared game-profile data, run native Save, close the isolated game, reopen it, and compare the restored pizza model.

Until those three actions are observed, Voice remains **Blocked** and Save/reload remains **Not run**.
