# PC2 Quarantine / PC3 Clean-Start Action Plan

**Scope: PC3 ONLY for active work.**

> Terminology note: voice dictation may say “PS2/PS3”; in this project that means **Pizza Connection 2 (PC2)** and **Pizza Connection 3 (PC3)**.

## Objective

Close any accidental PC2 work without allowing it to contaminate the active PC3 program, then continue only from clean PC3 / PC3 Pizza Creator work areas connected to the correct repositories.

## Current GitHub audit result

At the time this plan was written, the three active repositories were searched for `PC2`, `Pizza Connection 2`, and related markers. The PC2 references found are scope/policy guardrails that explicitly reject PC2 reuse; no active PC3 implementation file was identified as carrying PC2 game logic, asset contracts, catalogs, or reverse-engineering data.

Do **not** relabel valid PC3 code as PC2. If local Windows folders contain separate PC2 work that is not represented in these repositories, quarantine that work locally and publish it only to a repository/archive whose name is explicitly PC2.

## Hard separation rule

PC2 and PC3 are separate products and evidence domains.

### PC2 material

Any real PC2 work must be frozen and labeled with all of the following:

- repository/archive name contains `PC2` or `Pizza-Connection-2`;
- top-level documentation begins with `Scope: PC2 ONLY`;
- commits use `[PC2]` or `[PC2-ARCHIVE]` prefixes while being archived;
- no PC3 runtime profile, PathID, scene, asset count, catalog, schema, evidence, or release gate may be copied into it as if equivalent;
- PC2 material must not be pushed into any of the three PC3 repositories listed below.

If no explicit PC2 repository exists, keep the material quarantined locally rather than creating ambiguity inside a PC3 repository.

### PC3 material

Active work is allowed only in:

- `Ghenghis/PC3_Barros_Runtime_Proof_Studio` — ChatGPT-owned PC3 main runtime/evidence workstream;
- `Ghenghis/barros-workbench` — ChatGPT-owned PC3 Workbench workstream;
- `Ghenghis/Barros-Pizza-Creator` — Claude-owned PC3 Pizza Creator workstream.

Runtime profiles remain separate:

- main PC3 / Studio: `studio-1.11.403`;
- PC3 Pizza Creator: `creator-0.11.272`.

Neither profile may be substituted for the other.

## Windows workspace exit procedure

When leaving an old or uncertain work area:

1. **Stop all agents/tasks using the old work area.** Do not let a queued PC2 task continue after the scope change.
2. **Do not copy the old tree wholesale into PC3.** A dirty workspace can carry hidden configs, generated files, stale plans, local manifests, and wrong game assumptions.
3. Record its current Git status/HEAD if it is a Git checkout.
4. If it contains genuine PC2 work, freeze it in place or move it to a clearly named PC2 archive location. Do not delete it merely to clean PC3.
5. Give every retained PC2 note/report an explicit `PC2 ONLY` label.
6. Start the PC3 workstreams from clean Git checkouts/worktrees tied to the correct repositories.
7. Run the repository scope guard before any development or asset import.
8. Run the normal tests/audits before accepting the workspace as active.

## Canonical PC3 Windows roots

Use the real PC3 installations as the product roots:

- main PC3: `S:\Unity_Games\PC3`;
- PC3 Pizza Creator: `S:\Unity_Games\PC3 - Pizza Creator`.

Recommended isolated agent work areas beneath those roots:

- ChatGPT main PC3: `S:\Unity_Games\PC3\_agent-workspaces\chatgpt-pc3-main`;
- Claude Creator: `S:\Unity_Games\PC3 - Pizza Creator\_agent-workspaces\claude-pc3-creator`.

The work areas are repository working copies/tools; the stock/read-only game roots and exact build profiles remain authoritative for proof.

## Ownership after clean start

### ChatGPT — main PC3 only

Owns:

- Runtime Proof Studio;
- Barro’s Workbench;
- PC3 main extraction/catalog/PathID/runtime evidence;
- PC3 assets and application/restore chains;
- Windows-MCP orchestration for main PC3;
- ecosystem release aggregation;
- GitHub/GitLab parity evidence for the PC3 ecosystem.

ChatGPT does not implement Creator internals unless a shared contract requires a compatibility update.

### Claude — PC3 Pizza Creator only

Owns:

- `_pizza-agent`;
- Creator BepInEx/plugin/UI;
- Creator sidecar and provider integration;
- native recipe Preview/Restore/Apply/Save/Reload;
- Chef Voice microphone/STT;
- four Creator F8 modes and comparison reports;
- Creator All-stage proof.

Claude does not implement Runtime Proof Studio or Workbench internals.

## Git remote verification

Before work begins in a clean workspace, verify that `origin` resolves to the exact expected GitHub repository. Refuse to continue on a checkout whose remote does not match its assigned workstream.

GitLab publication remains a separate mirror step. Use each repository’s safe GitLab sync script only against an already configured `gitlab` remote; never guess the remote and never force-push divergent history.

## Contamination rules

The PC3 scope guard must fail active implementation/configuration if it finds:

- `PC2` as a product target;
- `Pizza Connection 2`;
- `Fast Food Tycoon 2`;
- `Pizza Tycoon 2`;
- PC2-specific asset/catalog/schema/runtime paths.

Guard/policy documents may mention those terms only to prohibit or quarantine them.

A PC2 screenshot, test, catalog, source conclusion, asset or runtime result can never satisfy a PC3 release gate.

## Documentation labeling policy

From this point forward:

- every new active PC3 handoff/plan/recovery document must identify itself as `Scope: PC3 ONLY` near the top;
- every retained PC2 archive document must identify itself as `Scope: PC2 ONLY` near the top;
- ambiguous unlabeled material from an old workspace is not authoritative until classified;
- current root `PC3_ONLY_SCOPE.md` and `WORKSTREAM_OWNERSHIP.md` take precedence over older plans.

## Completion checklist

The transition is complete only when:

- old/uncertain workspace tasks are stopped;
- any genuine PC2 work is quarantined and explicitly labeled PC2-only;
- clean PC3 work areas exist under the proper PC3 roots;
- each work area’s GitHub `origin` matches its assigned repository;
- PC3 scope guards pass;
- PC3 tests/audits are green or truthfully report remaining live gates;
- no PC2 material has been copied into the active PC3 repositories;
- Claude is working only in PC3 Pizza Creator and ChatGPT only in main PC3/Workbench/Studio.
