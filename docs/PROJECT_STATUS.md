# Barro's v1.4 factual status snapshot

Snapshot date: 2026-08-27 UTC. Authority: the real Steam v1.4 loader/UI/media run, the current 102-test suite, `artifacts/build-provenance.json`, `docs/V1_4_RUNTIME_PROOF_2026-08-27.md`, and `contracts/rc1.acceptance.json`.

| Area | State | Evidence boundary |
|---|---|---|
| Source/package completeness | Pass | 102 automated tests pass; the catalog contains 87 unique game ingredients in six categories and visual metadata for every item. |
| Exact supplied-assembly build | Pass | Windows `csc.exe` compiled the 1.4.0 plugin against the exact Creator 0.11.272 assemblies; artifact and provenance hashes agree. |
| BepInEx initialization/plugin Awake | Pass | The real Steam game loaded `Barro's AI Pizza Designer 1.4.0`; the sidecar started on `127.0.0.1:48173`. |
| Native fifth tab and panel geometry | Pass | The cloned tab remained 70×70. Runtime reports `panel left=1346`, `tab right=1340`, `gap=6`, so all five native tabs remain visible. |
| Pizza Art Studio | Pass | Seven built-in subjects, three detail levels, precision/organic styling, classic/vegan palettes and deterministic Remix are present. High-detail Santa compiled 176 exact placements and rendered recognizably in native 3D. |
| Focused Design Crew | Pass | The real MiniMax-connected Creative Director returned a concrete Arizona review on one call. A later live timeout returned the useful local Creative Director fallback within the bounded window. |
| Inspiration Library backend | Pass, empty | `/health` reports the capability, a 500-image ceiling, and `count=0`. No Facebook/export source has been imported yet. |
| Ingredient intelligence | Automated pass | Every exact catalog ingredient has flavor, dietary, allergen, display-name, color and geometry metadata; curated pairings, cohesion scoring and art-role palettes are tested. |
| Chat/Lab/Crew/Preview/Apply workflow | Pass with stated boundaries | Focused Crew, Santa Preview and Santa Apply ran in the real game. The older retained v1.1 proof covers base Chat/Lab/Restore. |
| Five-tab guided workspace | Pass | Chat exposes 6/8/12/18-step journeys and Professional/Playful/Goofball modes; AI Lab exposes Art Studio, Design Crew and Guided Build shortcuts; all five top tabs respond. |
| Barro's Media Deck | Pass | Five owner songs, non-destructive saved queue, ordering, shuffle/repeat, seek, volume, three-band tone, automatic inbox import and Stock/Barro's mutual exclusion work in the real game. |
| Media stability and quality | Pass | 5/5 audio-only 48 kHz stereo Vorbis q8 tracks decode and measure correctly. A 603.534-second live soak passed 21/21 process/health checks with zero relevant errors and automatic song progression. |
| Native Save/reload | Not run | Testing native Save may write shared user-profile game data, so it remains deliberately untouched. |
| Agent text-to-speech | Ready, not configured | A balanced 24-voice English roster, secure Azure request/WAV handling, mute, Speak and Stop are implemented. Music pause-before-speech/resume-after-speech is wired and tested statically. Current health says disabled/not probed, so audible playback is not claimed. |
| Microphone / speech-to-text | Blocked | Windows reports zero input devices and the configured text gateway has no dedicated STT endpoint. The UI says `No mic`; `/transcribe` fails closed. |
| Executed failures | Repaired | An initial provider timeout was bounded with local fallback. Media stutter risks were traced to hidden cover-art video streams, streaming/live waveform work and timestamps; output is now audio-only, fully decoded before play and timestamp-repaired. Final suite: 102/102. |

No API key value, Facebook image, or private source content is stored in this repository. The installed Inspiration Library is privacy-first and OFF by default; design-agent voices also start muted.

See `docs/V1_4_RUNTIME_PROOF_2026-08-27.md` for current media/runtime facts, `docs/V1_3_RUNTIME_PROOF_2026-08-27.md` for art/agent facts, and `docs/LIVE_RUNTIME_PROOF_2026-08-27.md` for the earlier base-workflow evidence.

The RC1 ledger includes v1.4 guided-workspace, media, audio-quality and speech-focus gates; optional Azure playback remains not run until the user supplies an Azure Speech resource.
