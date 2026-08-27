# Barro's v1.2 factual status snapshot

Snapshot date: 2026-08-27 UTC. Authority: the retained v1.1 end-to-end proof, the real Steam v1.2 loader/UI/health run, the current 71-test suite, `artifacts/build-provenance.json`, and `contracts/rc1.acceptance.json`.

| Area | State | Evidence boundary |
|---|---|---|
| Source/package completeness | Pass | 71 automated tests pass; the catalog contains 87 unique game ingredients in six categories. |
| Exact supplied-assembly build | Pass | Windows `csc.exe` compiled the 1.2.0 plugin against the exact Creator 0.11.272 assemblies; artifact and provenance hashes agree. |
| BepInEx initialization/plugin Awake | Pass | The real Steam game loaded `Barro's AI Pizza Designer 1.2.0`; the sidecar started on `127.0.0.1:48173`. |
| Native fifth tab and panel geometry | Pass | The cloned tab remained 70×70. Runtime reports `panel left=1346`, `tab right=1340`, `gap=6`, so all five native tabs remain visible. |
| Inspiration Library UI | Pass | `Ideas OFF` toggled to `Ideas ON`, changed its status text, and was returned to OFF after proof capture. |
| Inspiration Library backend | Pass, empty | `/health` and `/inspiration` report the v1.2 capability, a 500-image ceiling, and `count=0`. No Facebook/export source has been imported yet. |
| Ingredient intelligence | Automated pass | Every exact catalog ingredient has flavor, dietary, allergen, and display-name metadata; curated pairings and cohesion scoring are tested. No separate live provider request was made solely for this v1.2 smoke run. |
| Existing Chat/Lab/Crew/Preview/Restore/Apply workflow | Previously live-certified | Retained v1.1 evidence proves the end-to-end base workflow. This v1.2 run verified loader, UI, and health without repeating paid provider requests. |
| Native Save/reload | Not run | Testing native Save may write shared user-profile game data, so it remains deliberately untouched. |
| Microphone / speech-to-text | Blocked | Windows reports zero input devices and the configured text gateway has no dedicated STT endpoint. The UI says `No mic`; `/transcribe` fails closed. |
| Executed failures | None in final automated suite | 71 of 71 tests passed. Empty image source, Save/reload, and microphone/STT remain explicitly Empty/Not run/Blocked rather than being promoted to Pass. |

No API key value, Facebook image, or private source content is stored in this repository. The installed Inspiration Library is privacy-first and OFF by default.

See `docs/V1_2_RUNTIME_PROOF_2026-08-27.md` for the v1.2 runtime facts and `docs/LIVE_RUNTIME_PROOF_2026-08-27.md` for the earlier full base-workflow evidence.

The formal RC1 acceptance ledger predates this live v1.2 smoke run and must be regenerated before its aggregate gate counts are treated as current.
