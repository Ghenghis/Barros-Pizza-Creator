# RC1 factual status snapshot

Snapshot date: 2026-08-27 UTC. Authority: retained live evidence from the isolated Windows game copy, the current 65-test suite, `artifacts/build-provenance.json`, and `contracts/rc1.acceptance.json`.

| Area | State | Evidence boundary |
|---|---|---|
| Source/package completeness | Pass | 65 automated tests pass; the catalog still contains 87 unique game ingredients in six categories. |
| Exact supplied-assembly build | Pass | Windows `csc.exe` compiled the plugin against the exact Creator 0.11.272 assemblies; artifact and provenance hashes agree. |
| BepInEx initialization/plugin Awake | Pass | BepInEx 5.4.23.5 loaded `Barro's AI Pizza Designer 1.1.0` in the isolated game copy. |
| Fifth tab and Barro's header geometry | Pass | The cloned native tab rendered at 70×70 and the fitted 547-pixel header was retained in screenshots and runtime events. |
| Rounded UI and four mode views | Pass | Chat, AI Lab, Design Crew, and the truthful Chef Voice blocked state have separate retained 1920×1080 captures. |
| Chat | Pass | A live MiniMax-compatible request returned a valid `Sonoran Sunset` recipe and persisted to History. |
| AI Lab | Pass | A later live request returned three valid recipes with no fallback warning. |
| Design Crew | Pass with fallback | Four personas returned a 52% consensus. The online draft was invalid JSON, so the built-in game-valid designer supplied the recipe while the four-person review still completed. |
| Preview / Start Over / Apply | Pass | Runtime events prove a 12-placement preview, restoration of the captured pre-preview model, and a 9-placement apply. The native game screen retained the applied `Sonoran Sunset`. |
| Save/reload | Not run | Testing native Save would write shared user-profile game data outside the isolated copy, so it was deliberately left untouched. |
| Attachment parser | Automated pass | PNG/JPEG parsing, MIME-spoof rejection, metadata-only return, and chat attachment contract are tested. The native Windows file chooser was not separately exercised in the retained live run. |
| Microphone / speech-to-text | Blocked | Windows reports zero input devices and the configured text gateway has no dedicated STT endpoint. The UI now says `No mic` and offers `Retry microphone`; `/transcribe` fails closed. |
| Executed failures | None in final automated suite | 65 of 65 tests passed. The two environmental boundaries above remain explicitly Not run/Blocked rather than being promoted to Pass. |

No API key value is stored in this repository or the retained evidence. The live sidecar used an external token-file reference.

See `docs/LIVE_RUNTIME_PROOF_2026-08-27.md` for the exact event records, screenshot hashes, artifact hash, and pass/block matrix.

The formal RC1 acceptance ledger predates this live repair and must be regenerated before its aggregate gate counts are treated as current.
