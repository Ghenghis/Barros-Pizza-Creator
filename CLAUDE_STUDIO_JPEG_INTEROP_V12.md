# SCOPE: PC3 PIZZA CREATOR ONLY — Claude / Studio JPEG Interoperability v1.2

**Claude owns:** PC3 Pizza Creator exact-model executor, Creator-side source/runtime research, and all JRE state changes.  
**ChatGPT owns:** Runtime Proof Studio stimulus generation, evidence verification/observation, family analysis, next-action routing, and main-PC3 interoperability tooling.  
**Runtime:** `creator-0.11.272`  
**Rule:** Studio/Workbench implementation remains READ-ONLY to Claude.

## What changed in Studio

Studio now has one automated truth chain around the canonical E00–E10 research campaign:

```text
sealed exact stimulus
 -> Claude exact Creator execution receipt
 -> Studio independent receipt/model/action/assembly verification
 -> untouched stock UserData/JPEG observation
 -> Studio JPEG/pixel/DCT analysis
 -> Creator independent parser read-only
 -> Studio parser cross-validation
 -> fully_bound case
 -> experiment-family analysis
 -> JRE controlled-evidence readiness
 -> next-action routing
```

Claude should consume these results instead of creating a second campaign, observer, family analyzer, ledger, or next-action engine.

## Recommended agent query

When Studio ecosystem MCP v1.2 is available, ask:

```text
pc3_creator_jpeg_next_action
```

This is READ-ONLY. It returns the highest-value next action from:

```text
campaign state
E10 two-write state
family-measurement readiness
JRE controlled-evidence readiness
read-only Creator JRE contract state when locally accessible
```

Related read-only tools:

```text
pc3_creator_jpeg_campaign_status
pc3_creator_jpeg_next_case
pc3_creator_jpeg_family_analysis
pc3_creator_jpeg_jre_readiness
pc3_creator_jpeg_next_action
```

None of these tools edits Creator or promotes a JRE gate.

## Recommended Windows operator path

Studio control panel:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/CREATOR_JPEG_RESEARCH_CONTROL_PANEL.bat
```

Recommended button:

```text
RUN NEXT RESEARCH ACTION (Recommended)
```

Direct launcher:

```text
Ghenghis/PC3_Barros_Runtime_Proof_Studio/RUN_CREATOR_JPEG_NEXT_ACTION.bat
```

The dispatcher may launch a safe Studio-side action, but it refuses to auto-execute a Claude-owned JRE mutation/decision.

## Fully-bound remains the canonical case target

A case is not complete for family analysis merely because Studio observed a JPEG or both parsers agree.

Required strongest campaign state:

```text
fully_bound
```

which requires:

```text
exact current stimulus SHA
+ creator-0.11.272
+ Studio-independent verification of Claude's exact execution receipt
+ actual observed model/order/action/assembly agreement
+ stock native output observation
+ independent Creator/Studio JPEG parser agreement
```

Claude must keep emitting the shared execution receipt defined by:

```text
contracts/creator-controlled-execution-evidence.schema.json
```

## E10 is now a specialized two-write protocol

Do not treat a successful:

```text
Save -> reload exact model -> re-Save
```

receipt as proof that the two JPEGs are identical/different.

The stock game may overwrite the first JPEG before Studio's final UserData snapshot.

Studio now uses:

```text
CAPTURE_CREATOR_E10_ROUNDTRIP.bat
scripts/Watch-CreatorJpegWrites.ps1
scripts/match_creator_e10_jpeg_events.py
```

The watcher starts **before** E10 execution and retains every native JPEG write event.

Two separate native Saves may produce byte-identical files. Studio therefore does **not** deduplicate by hash alone. Write identity includes:

```text
native LastWriteTimeUtc ticks
+ byte size
+ SHA-256
```

Studio binds two distinct events to Claude's retained timestamps for:

```text
native_recipe_save
native_resave_after_reload
```

and independently cross-validates both selected JPEGs before comparing first-save vs re-save bytes/pixels/codec/DCT.

E10 family measurement readiness requires this specialized manifest; action/model round-trip success alone is no longer enough.

## One-piece geometry measurements now use native E00 as the baseline

Earlier per-case before/after measurement can be contaminated if the previous version of a recipe JPEG is not dough-only.

Studio family analysis now remeasures these Round one-piece families:

```text
E01 yaw
E02 X
E03 Z
E04 Y/depth
E07 size
```

against:

```text
first fully-bound E00 native dough-only JPEG = pixel baseline
second fully-bound E00 repeat = native save/render noise reference when available
```

using Studio's:

```text
pc3_creator_piece_measurement.measure_piece_change
```

This is the primary controlled pixel measurement for camera/yaw/size inference.

E08 shape is intentionally not measured against the Round E00 baseline because changing the dough shape changes the background/domain itself.

## Family-analysis truth layer

Studio now exposes:

```text
ANALYZE_CREATOR_JPEG_CAMPAIGN_FAMILIES.bat
pc3_creator_jpeg_family_analysis
```

Families:

```text
E00 repeated-save determinism
E01 yaw transfer
E02+E03 X/Z -> JPEG pixel mapping
E04 Y sensitivity
E05 overlap/order/depth
E06 explicit piece-count progression
E07 size footprint
E08 shape/framing
E09 A/B/C/D rotation/position/order differential
E10 native first-save/reload/re-save round trip
```

Family output uses only `fully_bound` current-corpus cases.

`measurement_ready=true` is **not** JRE PASS.

## JRE readiness v1.2

Studio's JRE board now separates three states:

```text
1. campaign inputs fully bound
2. mapped family measurement ready
3. source/runtime proof still required
```

Read-only surfaces:

```text
CREATOR_JPEG_JRE_READINESS.bat
pc3_creator_jpeg_jre_readiness
```

A Studio field such as:

```text
controlled_evidence_analysis_ready = true
```

means Studio's controlled-evidence portion is ready for Claude adjudication.

Only Claude may change:

```text
contracts/jpeg-reverse-engineering.acceptance.json
```

and only when the gate's own retained evidence requirement is truly satisfied.

## Static/runtime work remains separate

The controlled campaign cannot identify internal implementation by pixels alone.

Keep source/runtime research for:

```text
JRE-001 save-to-image call graph
JRE-002 final image write/texture assignment
JRE-003 camera/render target identity
JRE-004 render resolution/crop/resize/colorspace
JRE-005 JPEG API/quality/subsampling
JRE-009 depth/order mechanism when controlled output cannot distinguish causes
```

Use the existing Creator source-side tooling plus Studio read-only forensics. Do not infer an internal implementation merely from a fitted homography, DQT match, or visual similarity.

## Downstream decision gating

Studio's next-action router will not recommend JRE-014 until the read-only Creator contract says JRE-001 through JRE-013 are PASS.

It will not recommend JRE-015 final-document closeout until JRE-014 is PASS.

Studio never performs those Creator-owned mutations.

## Files to read from Studio when needed

READ-ONLY references:

```text
docs/CREATOR_JPEG_CANONICAL_RESEARCH_START_HERE.md
docs/CREATOR_JPEG_CANONICAL_CAMPAIGN_LEDGER.md
docs/CREATOR_JPEG_EXPERIMENT_FAMILY_ANALYSIS.md
docs/CREATOR_JPEG_E10_TWO_WRITE_ROUNDTRIP.md
docs/CREATOR_JPEG_NEXT_ACTION_ROUTER.md
```

## Ownership invariant

Claude:

```text
Creator implementation
exact-model executor
execution receipt producer
Creator source/runtime proof
JRE adjudication/final native JPEG document
```

ChatGPT / Studio:

```text
canonical stimulus producer
corpus sealing
independent execution verifier
stock-output observer
parser cross-validation
E10 write watcher/event binding
family measurements
readiness dashboards
next-action routing
```

Do not cross-edit implementation repositories. Exchange only shared contracts and retained evidence.
