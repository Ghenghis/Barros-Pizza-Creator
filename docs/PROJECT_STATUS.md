# Barro's v1.5 factual status snapshot

Snapshot date: 2026-08-27 UTC. Authority: the real Steam v1.5 loader/UI/media/crew run, the current 105-test suite, `artifacts/build-provenance.json`, `docs/V1_5_RUNTIME_PROOF_2026-08-27.md`, and `contracts/rc1.acceptance.json`.

| Area | State | Evidence boundary |
|---|---|---|
| Source/package completeness | Pass | 107 automated tests pass; the catalog contains 87 unique game ingredients in six categories and visual metadata for every item. |
| Exact supplied-assembly build | Pass | Windows `csc.exe` compiled the 1.5.0 plugin against the exact Creator 0.11.272 assemblies; artifact and provenance hashes agree. |
| BepInEx initialization/plugin Awake | Pass | The real Steam game loaded `Barro's AI Pizza Designer 1.5.0`; the sidecar started on `127.0.0.1:48173`. |
| Native fifth tab and panel geometry | Pass | The cloned tab remained 70×70. Runtime reports `panel left=1346`, `tab right=1340`, `gap=6`, so all five native tabs remain visible. |
| Pizza Art Studio | Pass | Seven built-in subjects, three detail levels, precision/organic styling, classic/vegan palettes and deterministic Remix are present. High-detail Santa compiled 176 exact placements and rendered recognizably in native 3D. |
| Design Crew | Pass | A final v1.5 live request rendered four separate agent responses and a 68% `Desert Fire` consensus. Sequential no-overlap voice playback is compiled/tested but awaits Azure Speech. |
| Inspiration Library backend | Pass, empty | `/health` reports the capability, a 500-image ceiling, and `count=0`. No Facebook/export source has been imported yet. |
| Ingredient intelligence | Automated pass | Every exact catalog ingredient has flavor, dietary, allergen, display-name, color and geometry metadata; curated pairings, cohesion scoring and art-role palettes are tested. |
| Chat/Lab/Crew/Preview/Apply workflow | Pass with stated boundaries | Focused Crew, Santa Preview and Santa Apply ran in the real game. The older retained v1.1 proof covers base Chat/Lab/Restore. |
| Five-tab guided workspace | Pass | Chat exposes 6/8/12/18-step journeys and Professional/Playful/Goofball modes; AI Lab exposes Art Studio, Design Crew and Guided Build shortcuts; all five top tabs respond. |
| Barro's Media Deck | Pass | Five owner songs, recursive albums, multiple named mixes, search/filter/sort, bulk organization, ordering, shuffle/repeat, seek, volume, three-band tone, automatic inbox import and Stock/Barro's mutual exclusion are present. Live `Christmas` search reduced 5 files to the one correct result. |
| Media stability and quality | Pass | 5/5 audio-only 48 kHz stereo Vorbis q8 tracks decode and measure correctly. A 603.534-second live soak passed 21/21 process/health checks with zero relevant errors and automatic song progression. |
| Native Save/reload | Not run | Testing native Save may write shared user-profile game data, so it remains deliberately untouched. |
| Agent text-to-speech | Ready, not configured | A balanced 24-voice roster, rate/gap/volume controls and a single sequential queue are implemented. One shared music-focus window prevents overlap. Current health says disabled/not probed, so audible playback is not claimed. |
| Microphone / speech-to-text | Hardware blocked | v1.5 adds device selection, Refresh, Live/Mute, gain and a real input meter. Windows reports zero input devices and the gateway has no dedicated STT endpoint, so capture remains unrun. |
| Executed failures | Repaired | One cramped bulk label found during the first v1.5 live pass was shortened and the exact artifact was rebuilt/reinstalled. Final suite: 107/107. |

No API key value, Facebook image, or private source content is stored in this repository. The installed Inspiration Library is privacy-first and OFF by default; design-agent voices also start muted.

See `docs/V1_5_RUNTIME_PROOF_2026-08-27.md` for current library/crew/microphone/runtime facts, `docs/V1_4_RUNTIME_PROOF_2026-08-27.md` for the long media soak, and `docs/V1_3_RUNTIME_PROOF_2026-08-27.md` for art/agent facts.

The proof ledger includes v1.5 large-library, named-playlist, roundtable and microphone-readiness coverage; optional Azure playback remains not run until the user supplies an Azure Speech resource.
