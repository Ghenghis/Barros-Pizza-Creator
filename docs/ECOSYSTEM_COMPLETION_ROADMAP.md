# Barro's PC3 ecosystem completion roadmap

> Historical v1.1 roadmap. The exact Creator source reconciliation and native JPG/recipe split are superseded by `docs/REVERSE_ENGINEERING_EVIDENCE.md` and `docs/NATIVE_PIZZA_JPEG_ALGORITHM.md`; live gates remain authoritative.

Date: 2026-08-24 America/Phoenix / 2026-08-25 UTC.

This roadmap governs three repositories:

- `Ghenghis/Barros-Pizza-Creator`
- `Ghenghis/barros-workbench`
- `Ghenghis/PC3_Barros_Runtime_Proof_Studio`

Machine-readable authority: `contracts/ecosystem.acceptance.json`.

## Completion rule

No percentage or “100% complete” statement is authoritative by itself. The ecosystem is complete only when every `release_required` gate in `contracts/ecosystem.acceptance.json` is `pass` with retained evidence. `not_run`, `blocked`, plans, source presence, mockups, generated documentation and inferred behavior are not passes.

## Current factual baseline

### Pizza Creator

The RC1 implementation exists and its current source/build ledger reports 7 pass, 1 blocked, 16 not run, 0 fail out of 24 release-required RC1 gates. The most recent GitHub Actions run after the PowerShell stderr-capture correction is green for both the portable contract and Windows static harness. Runtime/game gates remain deliberately unpromoted until executed on the target Windows build.

### Workbench

The existing PySide6 Workbench is functional as an asset/ComfyUI/MCP/agent tool, but at the start of this roadmap it does not contain a first-class `Barros-Pizza-Creator` service integration. Its agent knows its existing local tools and connected MCP tools; Pizza Creator-specific backend/status/proof actions must be added and tested.

### Runtime Proof Studio

The Studio already has PC3 extraction, truth-contract, runtime proof and GUI infrastructure, including the Hermes orchestration area. At the start of this roadmap it has no direct `Barros-Pizza-Creator` RC1 contract integration. It must consume the Creator contract/evidence rather than duplicate or reinterpret it.

## Work order

### Phase A — Freeze truth sources

1. Keep `contracts/rc1.acceptance.json` authoritative for Pizza Creator RC1 runtime certification.
2. Keep `contracts/ecosystem.acceptance.json` authoritative for cross-project completion.
3. Lock shared target facts used across repositories:
   - Pizza Creator build `0.11.272` / Unity `2017.3.1p4 x64` for the current RC1 target.
   - exact `Assembly-CSharp.dll` and firstpass SHA-256 values from the RC1 contract.
   - 87 valid ingredient IDs in six families.
   - `IPizzaCreatorService.LoadPizzaFromModel` as the native model application bridge.
   - no replacement of `Assembly-CSharp.dll`.
4. Any other PC3 stock-build extraction contracts used by Runtime Proof Studio remain separately versioned. They must never be silently merged with the Pizza Creator `0.11.272` target.

Evidence: committed contracts and automated fact-comparison output.

### Phase B — Complete Workbench integration

1. Add a small Qt-free Pizza Creator client module for local RC1 service health/history/chat/lab/crew/reload access.
2. Add Pizza Creator tools to the existing Workbench `ToolRegistry`; all tool results must come from the real service or report a real error.
3. Add editable configuration for Creator backend URL, target game folder, Creator project folder and evidence folder.
4. Add a compact, hideable Pizza Creator GUI surface to Workbench showing:
   - backend/provider state;
   - current RC1 gate summary when evidence exists;
   - quick Chat/Lab/Crew actions;
   - open game/evidence/project controls;
   - diagnostic/proof launch controls where the local platform supports them.
5. Preserve the existing Source / Tools+Chat / Output asset workflow.
6. Add tests for healthy service, unavailable service, JSON contract parsing, tool registration and failure behavior.
7. Run the full pre-existing test suite plus new tests.
8. Capture a real Workbench screenshot after launch showing the integrated panel.

Acceptance: WB-101 through WB-105 and VIS-402 all pass.

### Phase C — Complete Runtime Proof Studio integration

1. Add a Pizza Creator contract adapter that reads RC1 gate definitions/results without changing their meaning.
2. Add a visible Pizza Creator workspace/page to the existing Studio GUI.
3. Surface:
   - RC1 pass/fail/blocked/not-run counts;
   - latest evidence bundle path;
   - BepInEx log availability;
   - F8 Chat/Lab/Crew/Voice screenshots;
   - F9 saved/reload verification;
   - reference-image comparison reports/diffs.
4. Wire supported local actions to the existing Creator installer/diagnose/proof scripts through explicit paths and subprocess argument lists; never shell-concatenate untrusted values.
5. Add evidence ingestion tests using fixtures and retain true state semantics.
6. Run Studio’s existing tests plus new integration tests.
7. Capture a real Studio screenshot showing the Pizza Creator workspace.

Acceptance: ST-201 through ST-205 and VIS-403 all pass.

### Phase D — Live Pizza Creator certification

Run the RC1 Windows acceptance flow on the exact target installation:

1. installation/diagnostic verification;
2. BepInEx initialization and plugin `Awake`;
3. fifth tab placement and Barro’s title geometry;
4. Chat generation using exact catalog IDs;
5. Preview → restore → apply;
6. native recipe-book save and stock reload;
7. microphone enumeration/capture plus configured STT response;
8. image attachment through a vision-capable configured provider;
9. F8 capture in Chat, Lab, Crew and Voice;
10. F9 exact saved/reloaded model verification;
11. objective reference-image comparisons and retained diff images.

Any failure stays `fail`; unavailable hardware/service stays `blocked`; anything not executed stays `not_run`.

Acceptance: all 24 gates in `contracts/rc1.acceptance.json` pass and therefore E0-001 plus VIS-401 pass.

### Phase E — Cross-project gap audit

Run a cross-project audit that verifies:

1. target/version/hash facts are not contradictory;
2. 87-item catalog facts agree;
3. provider names/endpoints are treated as configuration, not hard-coded claims of availability;
4. no project calls mockups or source code runtime proof;
5. all generated screenshots are labeled reference vs live;
6. Workbench and Studio both point to the Creator contract/evidence semantics;
7. no TODO/placeholder/stub path is exposed as a completed user feature;
8. documentation matches actual executable entry points.

Acceptance: SYNC-301 through SYNC-303 pass with a retained report.

### Phase F — Clean-install/reproducibility sweep

1. Regenerate Pizza Creator RC1 release ZIP and verify manifest, hashes and CRCs.
2. Exercise Workbench `doctor`, setup, launch and tests from a clean checkout/environment.
3. Exercise Studio doctor/setup/launch/tests from a clean checkout/environment.
4. Retain logs and screenshots from all three applications.

Acceptance: PKG-501 through PKG-503 pass.

### Phase G — Publication and parity

1. Commit only reviewed changes.
2. Push each project to its GitHub `main` and record remote commit SHA.
3. Require green CI where configured.
4. Publish/mirror to GitLab only through an authenticated write path.
5. Preserve existing GitLab history; do not force-push over unrelated commits.
6. Compare remote SHAs/content snapshots and retain the parity report.

Acceptance: PUB-601 through PUB-604 pass.

## Snapshot contract

The final proof set must contain, at minimum:

- live Pizza Creator Chat screenshot;
- live Pizza Creator AI Lab screenshot;
- live Pizza Creator Design Crew screenshot;
- live Pizza Creator Chef Voice screenshot;
- Pizza Creator fifth-tab/header geometry captures;
- preview/apply/restore/reload captures required by RC1;
- Workbench integrated GUI screenshot;
- Runtime Proof Studio integrated GUI screenshot;
- difference images/reports for all four Pizza Creator reference modes.

Every screenshot must come from a real running executable. Mockups remain baselines only.

## Bug/gap policy

When a bug is found:

1. retain the failing evidence;
2. mark the corresponding gate `fail` rather than weakening the gate;
3. correct the smallest responsible layer;
4. add or strengthen a regression test where possible;
5. rerun affected and adjacent gates;
6. retain before/after evidence;
7. only then promote the gate to `pass`.

## Final definition of done

The work is 100% complete only when:

- all 24 Pizza Creator RC1 gates pass;
- WB-101..105 pass;
- ST-201..205 pass;
- SYNC-301..303 pass;
- VIS-401..403 pass;
- PKG-501..503 pass;
- PUB-601..604 pass;
- retained live screenshots and evidence make every claim independently inspectable.
