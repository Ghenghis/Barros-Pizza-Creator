# Barro's v1.6 factual status snapshot

Snapshot date: 2026-08-27 UTC. Authority: the exact Steam loader/UI/media run, Unity 2021 authoring/export log, 115-test suite, `artifacts/build-provenance.json`, `docs/V1_6_RUNTIME_PROOF_2026-08-27.md`, and `contracts/rc1.acceptance.json`.

| Area | State | Evidence boundary |
|---|---|---|
| Source/package completeness | Pass | 115/115 automated tests pass; exact catalog and v1.6 media/voice/authoring contracts are present. |
| Exact supplied-assembly build | Pass | Windows compiler built the 157,184-byte plug-in against Creator 0.11.272; artifact/provenance SHA-256 is `520c67b...15895`. |
| BepInEx initialization/plugin Awake | Pass | Exact game loaded BepInEx 5.4.23.5 and Barro's Designer 1.6.0, started the backend and injected the live bridge. |
| Native fifth tab and panel geometry | Pass | `left=1346`, `right=1920`, `tab_right=1340`, `gap=6`; all native/add-on tabs remain visible at 1080p. |
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

## v1.7 development continuation

The stable release remains v1.6. On branch `codex/barros-v1.7-animation-lab`, the next authoring milestone is complete: Unity 2021 generated a hash-listed 256×32 connection-pulse strip and schema-v2 JSON, the plug-in compiled against the exact Creator assemblies, 116/116 tests passed, and the exact game retained `ui.exported_animation_loaded` for eight frames at 8 fps. See `docs/V1_7_ANIMATION_CHECKPOINT_2026-08-27.md`. This is an isolated development checkpoint, not a replacement v1.7 release ZIP.
