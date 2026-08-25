# Claude Next Tasks — PC3 Pizza Creator

**Owner:** Claude  
**Workstream:** PC3 Pizza Creator only  
**Do not work on:** Runtime Proof Studio, Barro's Workbench implementation, or any PC2 / Fast Food Tycoon 2 material.

Canonical ownership: `contracts/workstream-ownership.json`.

## Current starting point

The `_pizza-agent` Slice 1 backend is already implemented and reviewed. Finish the active Slice-1 housekeeping/polish batch first, keep its tests green, and then proceed through the tasks below in order.

The Creator's native/runtime facts are in `CLAUDE_HANDOFF.md`. The release truth source is `contracts/rc1.acceptance.json`; only retained evidence may promote a gate.

## Secret-handling rule

Do not inspect, enumerate, print, commit, or document credential directories or credential filenames. Do not ask the operator to reveal token values or credential filenames. Use the existing `pizza_agent.secrets` runtime-loading abstraction, environment variables, OS credential helpers, or an explicitly supplied runtime path outside version control. Error messages must remain masked. Never include credentials in logs, prompts, evidence, commits, CI variables, or handoff documents.

---

# Priority 0 — Finish Slice-1 housekeeping

Complete the already-started housekeeping/polish task from the Slice-1 reviews.

Acceptance:

- Python suite remains green.
- .NET verifier suite remains green.
- No regression of the corrected native `IngredientSize` mapping: `Large=0`, `Medium=1`, `Small=2`.
- No regression of the `PizzaSauce` prompt handling fix.
- No secret values or secret paths enter tests/logs.
- Commit the housekeeping changes as one focused commit or a small sequence of reviewable commits.

Retain a compact `evidence/claude/slice1-housekeeping.json` containing commit SHA(s), test counts, build result, and no secrets.

---

# Priority 1 — Align pizza-agent output with the real Creator runtime contract

The Slice-1 interchange format must feed the actual native Creator bridge instead of becoming a second recipe authority.

Implement/verify:

1. Map `pizza.final.json` into the exact Creator/native model contract described by `CLAUDE_HANDOFF.md`.
2. Use only the real 87 ingredient IDs and real shape dough positions.
3. Keep ingredient amount units in grams.
4. Preserve the corrected `IngredientSize` enum values.
5. Preserve position + rotation data required to build `IngredientContainerModel` instances.
6. Do not synthesize cost/taste/profit authority in Python when the running game can provide native values.
7. Add a deterministic cross-check fixture proving Python final JSON -> .NET verifier -> Creator bridge agree on IDs, shape, size, amount, placement and rotation.

Deliverables:

- versioned interchange schema if the current schema is insufficient;
- Python tests;
- .NET tests;
- a short compatibility note in `docs/`;
- no parallel fake native-model implementation.

---

# Priority 2 — Connect pizza-agent to the existing Creator sidecar/plugin

Make Slice 1 usable from the existing unified Creator UI rather than as a separate CLI-only product.

Requirements:

- Reuse the existing Creator sidecar/provider routing and native plugin.
- Add a bounded internal adapter for compose/render/verify requests.
- Keep Offline, local OpenAI-compatible/LM Studio, Ollama, hosted OpenAI-compatible and Anthropic/provider routing compatible with the existing Creator design.
- Return explicit errors; never fabricate success when a provider, verifier or runtime bridge fails.
- Do not duplicate the Workbench or Studio agent servers.
- Preserve the existing Creator API truth surfaces including `/health`, `/history`, `/proof/latest`, `/inspect-attachment`, `/compose`, `/chat`, `/lab`, `/crew`, `/transcribe`, `/reload`, `/shutdown`.

Acceptance:

- a pizza-agent-produced recipe can be requested through the existing Creator integration path;
- the exact verifier report is retained;
- the UI receives a validated recipe suitable for native Preview, not a flat image pretending to be the pizza.

---

# Priority 3 — Finish the unified fifth-tab UI implementation

Implement the real in-game UI for all four modes, using the already-approved references as geometry/visual targets:

- Chat
- AI Lab
- Design Crew
- Chef Voice

Requirements:

- fifth tab registered through the real `TabBar.RegisterTab(Tab)` route;
- BARRO'S PIZZA CREATOR header only while the AI tab is active;
- close button remains clear;
- stock Bakehouse header is restored on stock tabs;
- no mock-only controls;
- controls wire to real sidecar/native actions;
- no clipping at the target game resolution/layout;
- retain F8 evidence for each mode.

Do not rewrite the game's main assembly merely to add the tab if the BepInEx plugin route remains viable.

Target contract gates: `UI-301`, `UI-302`, `UI-303`, then `VIS-601` through `VIS-604` once live.

---

# Priority 4 — Complete native Preview / Restore / Apply

Use the actual game model/service path documented in `CLAUDE_HANDOFF.md`.

Requirements:

- Preview snapshots the current real `PizzaModel`, then uses `IPizzaCreatorService.LoadPizzaFromModel(PizzaModel)` with the validated AI recipe.
- Restore returns to the exact captured pre-preview model.
- Apply intentionally commits the selected validated recipe.
- Runtime events identify each operation and whether it succeeded.
- Fail closed on invalid recipe/model/verifier state.

Target gates: `ACT-401`, `ACT-402`, `ACT-403`.

Retain:

- `runtime-events.jsonl`
- `preview.png`
- `restore.png`
- `apply.png`
- hash/identity of the recipe used.

---

# Priority 5 — Complete native Save + exact reload verification

Requirements:

- Save invokes the native recipe-book operation, not direct file rewriting.
- Reload the saved AI recipe through the stock/native route.
- F9 or equivalent comparison must compare the real modeled state and require exact name, shape, placements and profit-factor agreement.
- Do not mark PASS from source inspection.

Target gates: `ACT-404`, `ACT-405`.

Retain `saved-reload.json`, runtime events and `reload.png`.

---

# Priority 6 — Complete real Chef Voice microphone/STT path

Requirements:

- enumerate a real Windows microphone device;
- capture non-empty PCM/audio;
- send bounded audio through the configured Creator `/transcribe` path;
- obtain a non-empty transcript;
- use that transcript as the recipe prompt;
- retain provider/configuration truth separately from reachability/success;
- never place credential values in evidence.

Target gates: `VOX-501`, `VOX-502`.

Retain runtime event evidence plus the Voice-mode F8 screenshot. Audio evidence should contain metadata/hash/size as needed, not secret/provider credentials.

---

# Priority 7 — Run the exact Windows build/loader proof before UI certification

Use `contracts/rc1.acceptance.json` and `scripts/Invoke-ProofContract.ps1` as authority.

Run the exact target game build only. Do not mix Studio `studio-1.11.403` facts into Creator `creator-0.11.272`.

Prove/retain:

- `BLD-101` exact assembly hashes;
- `BLD-102` zero-error plugin compile;
- `BLD-103` prebuilt plugin/provenance agreement;
- `BLD-104` Windows compiler parity;
- `RUN-201` BepInEx 5 x64 initialization;
- `RUN-202` plugin discovered + Awake without relevant exception.

If any exact hash differs, stop runtime promotion and record the mismatch.

---

# Priority 8 — Capture and compare the four real Creator modes

After the live fifth tab is running:

1. open Chat and capture F8;
2. open AI Lab and capture F8;
3. open Design Crew and capture F8;
4. open Chef Voice and capture F8;
5. run the repository comparison harness against the locked references;
6. fix real geometry/clipping/content issues, then recapture;
7. retain comparison reports.

Target gates: `VIS-601`, `VIS-602`, `VIS-603`, `VIS-604`.

A screenshot from a mock, test host or offscreen renderer is not sufficient.

---

# Priority 9 — Creator All-stage proof and truthful release state

Run the Creator proof harness at `Stage All` with the exact Creator game root and `RequireComplete` only when all live tasks really have retained evidence.

Requirements:

- no manually changing gate states to PASS;
- `/proof/latest` must expose the retained result;
- all release-required Creator gates must PASS before runtime-certified is true;
- if a gate is blocked, leave it blocked/not_run with the reason and continue fixing it rather than weakening the contract.

Deliverables to ChatGPT's PC3-main workstream:

- final Creator main SHA;
- `_pizza-agent` SHA/identity if it remains a separate repository/worktree;
- Creator `results.json` / retained proof location;
- `/proof/latest` certification summary;
- four F8 screenshots + comparison reports;
- Preview/Restore/Apply/Save/Reload evidence paths;
- Voice proof paths;
- any schema/handoff change ChatGPT must consume.

---

# Priority 10 — Publication

Once Creator tests and retained proof are consistent:

- commit all Creator-only changes;
- push to the configured GitHub Creator repository using existing authenticated Git tooling/credential helpers;
- use the repository's safe GitLab sync script only when the configured `gitlab` remote exists and histories are compatible;
- never force-push divergent GitLab history;
- never read or print token files to accomplish publication.

If GitLab authentication is unavailable, report publication as blocked with the local/GitHub SHA; do not invent parity.

---

# Cross-workstream boundary with ChatGPT

Claude should **not** implement or redesign:

- Runtime Proof Studio v1.2;
- Barro's Workbench v2.3;
- PC3 main extraction/PathID cataloging;
- Workbench -> Studio image handoff implementation;
- PC3 main Windows-MCP orchestration;
- ecosystem release-ledger aggregation.

ChatGPT owns those items.

Claude may read their contracts/evidence only when necessary to keep Creator integration compatible.

When Creator changes a shared schema/API, document the exact delta and hand it to ChatGPT rather than editing a competing implementation in the PC3-main repositories.
