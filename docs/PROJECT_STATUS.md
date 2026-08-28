# Barro's v1.6 factual status snapshot

Snapshot date: 2026-08-27 UTC. Authority: the exact Steam loader/UI/media/header run, Unity 2021 authoring/export log, 121-test complete suite, isolated Windows installer lifecycle proof, `artifacts/build-provenance.json`, `docs/V1_6_RUNTIME_PROOF_2026-08-27.md`, and `contracts/rc1.acceptance.json`.

| Area | State | Evidence boundary |
|---|---|---|
| Source/package completeness | Pass | 121/121 automated tests pass; exact catalog and v1.6 media/voice/authoring/Windows packaging/final-header contracts are present. |
| Windows Setup and portable release | Pass | Real Setup EXE and offline portable ZIP built. Isolated clean install, exact plug-in hash, private Python, settings-preserving repair and safe uninstall all pass. Commercial game files are absent. |
| Exact supplied-assembly build | Pass | Windows compiler built the 157,184-byte plug-in against Creator 0.11.272; artifact/provenance SHA-256 is `c052adc8...7d54bb`. |
| BepInEx initialization/plugin Awake | Pass | Exact game loaded BepInEx 5.4.23.5 and Barro's Designer 1.6.0, started the backend and injected the live bridge. |
| Native fifth tab and panel geometry | Pass | `left=1346`, `right=1920`, `tab_right=1340`, `gap=6`; all native/add-on tabs remain visible at 1080p. |
| Complete centered header | Pass | Live 1920×1080 proof shows the 1280×143 header with chef, complete text and both end caps. It is centered 39 px left of panel-center to reserve the native 78 px close area and enlarged by 8 px without covering tabs. |
| Unity UI authoring lab | Pass | Unity 2021.3.45f2 generated the interactive five-page scene and passed a Play-mode tab/action inspection. |
| Unity 2017 compatibility export | Pass | Five hashed PNG skins plus JSON exported; exact runtime logged `ui.exported_theme_loaded`; invalid assets retain built-in fallbacks. |
| Pizza Art Studio / ingredient intelligence | Pass | Seven subjects, three detail levels, deterministic placement, 87 exact ingredients and validated metadata/pairings remain covered. |
| Design Crew/provider | Pass with fallback boundary | Direct MiniMax Chat/Crew passed. Four sequential Azure voices passed. One in-game Crew request used the local deterministic fallback. |
| Chef Voice / microphone | Partial | Azure synthetic TTS→STT passed and Turtle Beach P11 capture opened. No physical spoken phrase was recognized in the retained attempt. |
| Media Deck audio | Pass | Five-song playback, search/playlist/tone/transport UI and Stock/Barro's one-source exclusivity pass; current live run played the first OGG. |
| Lyric video | Pass | Four H.264/AAC files fully decode; exact-game Casa Grande prepare/play/pause/resume/seek/Lyrics Off/On passed. |
| Audio-only timed lyrics | Code pass, content pending | LRC parser/highlighter is tested and synchronized to playback. OCR draft was rejected; no inaccurate LRC shipped. |
| Compact 1080p layout | Pass | Media starts compact; track controls wrap; no horizontal library scroller; live proof image shows the lower controls inside the panel. |
| Native Save/reload | Not run | Deliberately untouched because it writes shared user-profile game data. |
| Inspiration Library | Pass, empty | Capability/limits remain available; no private images were imported. |

No API key value, private source file, OCR draft, Facebook image or Unity cache is stored in the repository. The Unity lab does not reconstruct the compiled game, and no Unity 2021 AssetBundle is sent to the Unity 2017 Player.
