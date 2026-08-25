# SCOPE: PC3 PIZZA CREATOR ONLY — Claude Access and Location Map

Owner: Claude
Primary repository: Ghenghis/Barros-Pizza-Creator
Primary runtime profile: creator-0.11.272
Primary product: Pizza Connection 3 - Pizza Creator

This file tells Claude where relevant data lives and what access mode is allowed. Presence of a path, folder, or remote does not prove that credentials or network access are currently working. Verify access before use. Follow PC3_ONLY_SCOPE.md and contracts/workstream-ownership.json at all times.

## 1. Claude WRITE locations — Creator work only

### Local Windows product root
- S:\Unity_Games\PC3 - Pizza Creator
- Purpose: exact Pizza Creator game build, Managed assemblies, BepInEx/runtime installation, screenshots, runtime proof, audio conversion and Creator-specific assets.
- Allowed: Creator-only runtime inspection and Creator-only generated artifacts.

### Local pizza-agent workspace
- S:\Unity_Games\PC3 - Pizza Creator\_pizza-agent
- Purpose: composer / solver / scoring / image backend / verifier / CLI / tests.
- Allowed: Creator-only implementation and tests.

### Isolated clean Claude workspace
- S:\Unity_Games\PC3 - Pizza Creator\_agent-workspaces\claude-pc3-creator
- GitHub origin must be: Ghenghis/Barros-Pizza-Creator
- Branch: main unless an explicit task says otherwise.
- This is the preferred clean working copy after the isolation bootstrap has been run.

### Creator audio
- S:\Unity_Games\PC3 - Pizza Creator\Barros_Music
- User-owned audio staging only.
- Use CONVERT_BARROS_MUSIC.bat for decode-validated Ogg conversion and hashes.

## 2. GitHub — Claude WRITE vs READ-ONLY

### WRITE
- Ghenghis/Barros-Pizza-Creator
- Claude owns implementation here.
- Before push: run the repository PC3 scope guard and Creator test/proof gates applicable to the change.

### READ-ONLY integration reference
- Ghenghis/PC3_Barros_Runtime_Proof_Studio
- Owner: ChatGPT
- Purpose for Claude: read shared contracts, runtime evidence interfaces, build-profile boundaries, Creator bridge expectations, and release evidence only.
- Claude must not implement Studio features here unless the user explicitly changes ownership.

### READ-ONLY integration reference
- Ghenghis/barros-workbench
- Owner: ChatGPT
- Purpose for Claude: read image-handoff schema, Creator integration expectations, exact-format requirements, and shared release evidence only.
- Claude must not implement Workbench features here unless the user explicitly changes ownership.

## 3. GitLab — Creator publication route

- Creator repository contains SYNC_GITLAB_SAFE.bat and scripts/Sync-GitLabSafe.ps1.
- Expected remote name: gitlab.
- The script never guesses a GitLab URL, never force-pushes, fetches first, checks ancestry, and verifies the remote SHA after a normal push.
- Access state: VERIFY FIRST in Claude's Windows checkout by checking whether the gitlab remote exists and is reachable using existing authenticated Git credentials.
- Never expose tokens, remote credentials, credential files, or secret values in logs, prompts, evidence, commits, or handoffs.

## 4. Google Drive — verified PC3 locations visible to the connected Drive account

The following folder IDs were observed through the connected Google Drive integration. Claude may use them only according to ownership and scope below. Claude Desktop access to the same Google account must still be verified in Claude's environment; a known folder ID is not proof that Claude Desktop is authenticated.

### Creator-focused Drive locations — Claude may READ / DOWNLOAD / compare; WRITE only when explicitly requested
- Pizza Connection 3 - Pizza Creator — folder id: 1zAHcpULXovkopFMIXz0W_DXTdgMoQYKt
- Pizza Connection 3 - Pizza Creator_Data — folder id: 1byIjaEJSmSnpoEr6cVfLz8E-Qol1N57z
- PizzaCreator — folder id: 1b0Befs16f1gbV7CbEvQUwoU_bJYPCcZY
- Barros_Pizza_Creator_RC1_Workbench_4.1_Studio_1.1_2026-08-24 — folder id: 1sOexinkTs-5Sb7S39cEbp_N11iguV6uW
- PC3_Barros_Agent_Continuation_Handoff_v4.1 — folder id: 1Lqp5LQPOn8_YKq1qJ8mCu8rMCI7VpEID

### Main PC3 Drive locations — READ-ONLY integration reference for Claude
- Pizza Connection 3 — folder id: 1YWxVWFVBpTQeG_HyfT21eZwIB3jfn79-
- Pizza Connection 3_Data — folder id: 1G8gWfjKMJlPpZDUOX4HqEZtuu3Hnlen7
- PC3_Extraction_Output_v0.5 — folder id: 1NQiz2cbq_nQuystcywFcSLWlJlQm85wT
- Tools — folder id: 1cJtVQm015MCofjJzbKOonNl-JezM4UyE
- Chatgpt_Asset_Collection — folder id: 14SjRZN4gxekHzP_jUwOYw-sgKl_yG3wg

Main-PC3 Drive material is owned by ChatGPT's Studio/Workbench workstream. Claude may inspect it only when necessary to preserve Creator compatibility. Claude must not treat main-PC3 extraction data as Creator runtime truth unless the Creator build contract independently verifies the same fact.

## 5. Exact Creator runtime identity

- Creator build profile: creator-0.11.272
- Unity: 2017.3.1p4 x64
- Steam app id: 851330
- Assembly-CSharp SHA-256: ebf8698df7cb4af904c98c299994705ea529efbdf1e8ccb3e7ca8cb42a1cbc1c
- Assembly-CSharp-firstpass SHA-256: f9cbf0951fc4d4b0788c47bbe41a3820fa333d293175bbb7cb398eb4728fd284
- Authority: contracts/rc1.acceptance.json and scripts/Invoke-ProofContract.ps1

Never substitute Studio profile studio-1.11.403 for Creator proof.

## 6. Creator services and local integration surfaces

Default Creator sidecar:
- http://127.0.0.1:48173

Known endpoints:
- /health
- /history
- /proof/latest
- /inspect-attachment
- /compose
- /chat
- /lab
- /crew
- /transcribe
- /reload
- /shutdown
- /contract

Reachability alone is not runtime proof.

## 7. Windows-MCP / desktop automation

- Windows-MCP is an external sidecar/tool source used for live Windows/game interaction.
- Historical/default config location in this ecosystem: S:\MCP\windows-mcp\config.json
- Common local transport noted by the Studio integration: http://127.0.0.1:8080/sse or configured stdio transport.
- Access state: VERIFY FIRST in Claude Desktop. Transport detection is not evidence that an in-game action occurred.
- Claude may use Windows-MCP for Creator-only desktop/game actions and evidence capture.
- Studio/Workbench automation remains ChatGPT-owned.

## 8. Secrets and credentials

- Do not inspect, enumerate, print, commit, or document secret directories, token filenames, or token values.
- Use pizza_agent.secrets runtime loading, environment variables, OS credential helpers, or an explicitly supplied runtime path.
- GitHub, GitLab, provider, Google, or other credentials must never enter evidence JSON, screenshots, prompts, commits, test fixtures, or handoff documents.
- A credential's existence must not be inferred from a directory listing.

## 9. Shared handoff boundaries to ChatGPT

Claude must hand ChatGPT only the integration facts needed by the main PC3 workstream:
- Creator main commit SHA
- pizza-agent commit/worktree identity
- Creator contract/proof result location
- /proof/latest summary
- exact schema/API deltas
- four live Creator mode screenshot evidence paths when available
- Preview / Restore / Apply / Save / Reload evidence locations
- Voice evidence locations
- any Creator-originated image-handoff or runtime compatibility change

Claude must not edit Studio or Workbench merely to consume its own schema change. Document the delta and hand it to ChatGPT.

## 10. Access verification checklist at session start

Claude should verify, without exposing credentials:
1. Current working directory is under the Creator product root or isolated Creator workspace.
2. Git origin is Ghenghis/Barros-Pizza-Creator.
3. Current build profile is creator-0.11.272.
4. Root PC3-only marker and contracts are present.
5. Creator game root exists and exact assembly hashes match before runtime certification.
6. Google Drive Creator folder is reachable if Drive data is needed.
7. GitHub push authentication is available before publication.
8. GitLab remote/authentication is verified before safe sync; otherwise report blocked.
9. Windows-MCP is reachable only if a live desktop action is required.
10. No main-PC3 Studio/Workbench location is being used as a writable Creator workspace.

Fail closed when any identity is ambiguous.