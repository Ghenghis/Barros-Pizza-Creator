# RC1 factual status snapshot

Snapshot date: 2026-08-25 UTC. Authority: `contracts/rc1.acceptance.json` plus the latest retained Static and Build runs.

| Area | State | Evidence boundary |
|---|---|---|
| Source/package completeness | Pass | Required files present, 20 tests pass, 87 unique ingredients in six categories, four mockup hashes locked |
| Exact supplied-assembly build | Pass | Zero-error Roslyn build, output/provenance hashes agree |
| Windows compiler parity | Blocked | Requires `csc.exe` and installed game DLLs on the target Windows host |
| BepInEx initialization/plugin Awake | Not run | Requires the target process and `BepInEx\LogOutput.log` |
| Fifth tab and Barro's header geometry | Not run | Requires live runtime events and screenshots |
| Preview/Restore/Apply/Save/reload | Not run | Requires real 3D state changes and the saved-model comparison |
| Microphone and configured STT | Not run | Requires a real Windows device and provider response |
| Four live mockup comparisons | Not run | Requires F8 captures from the running game |
| Executed failures | None | No executed contract gate failed |

Combined ledger: **7 pass, 1 blocked, 16 not run, 0 fail** out of 24 release-required gates.

“No failed gates” does not mean “no remaining blockers.” The remaining blocker is access to the target Windows runtime. Once the package is run there, every pending state can become an observed pass or an actionable failure with retained proof.
