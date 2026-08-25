# SCOPE: PC3 PIZZA CREATOR ONLY — Claude Handoff

> **Repository:** `Ghenghis/Barros-Pizza-Creator`  
> **Owner:** Claude  
> **Runtime profile:** `creator-0.11.272`  
> **Windows product root:** `S:\Unity_Games\PC3 - Pizza Creator`  
> **Isolated workspace:** `S:\Unity_Games\PC3 - Pizza Creator\_agent-workspaces\claude-pc3-creator`  
> **Current execution queue:** `CLAUDE_NEXT_TASKS_PC3_CREATOR.md`  
> **Machine-readable queue:** `contracts/claude-creator-task-queue.json`  
> **Complete access/location map:** `CLAUDE_ACCESS_MAP_PC3_CREATOR.md`  
> **Machine-readable access map:** `contracts/claude-access-map.json`  
> **Verified shared Google Drive root ID:** `1v_EZAxzNZQbi5DjpwWxBTiMyPHaIut34`  
> **Ownership:** Claude owns PC3 Pizza Creator. ChatGPT owns Runtime Proof Studio, Barro's Workbench, and the main PC3 ecosystem. Studio/Workbench/main-PC3 locations are READ-ONLY integration references for Claude unless the user explicitly changes ownership.  
> **Forbidden:** Pizza Connection 2 / Fast Food Tycoon 2 work unless the user explicitly changes scope.

## Access rule — read this before doing any work

Claude has a complete map of the known local, Google Drive, GitHub, GitLab, Creator-sidecar, and Windows-MCP locations in `CLAUDE_ACCESS_MAP_PC3_CREATOR.md` and `contracts/claude-access-map.json`.

A documented location is **not** proof that Claude Desktop is authenticated to it. At the beginning of a session, verify access without exposing credentials. Use these access modes exactly:

- **WRITE:** PC3 Pizza Creator local product root, `_pizza-agent`, isolated Claude Creator workspace, Creator GitHub repository, and Creator-specific Drive folders only when the task explicitly requires a Drive write.
- **READ-ONLY / INTEGRATION:** Runtime Proof Studio, Barro's Workbench, main PC3 local roots, main PC3 Google Drive folders, extraction outputs, shared contracts, and ecosystem evidence.
- **VERIFY FIRST:** Google Drive authentication in Claude Desktop, GitHub push authentication, configured GitLab remote/authentication, and Windows-MCP reachability.
- **DENIED:** any subtree or project excluded by `PC3_ONLY_SCOPE.md` / `contracts/pc3-only-scope.json`.

The verified shared Google Drive root contains separate Creator and main-PC3 folders. Use the exact folder IDs in the access map. Never infer that a similarly named Drive folder is the same target. The access map also contains a denied Drive subtree ID so an agent cannot accidentally traverse outside the locked PC3 program scope.

For GitLab, use only `SYNC_GITLAB_SAFE.bat` / `scripts/Sync-GitLabSafe.ps1`. The remote name is normally `gitlab`, but the URL is intentionally not guessed or committed. Fetch first, verify ancestry, never force-push, and verify the remote SHA after a normal push.

Before editing, read `00_READ_FIRST_PC3_ONLY.md`, `PC3_ONLY_SCOPE.md`, `WORKSTREAM_OWNERSHIP.md`, `contracts/pc3-only-scope.json`, `contracts/workstream-ownership.json`, `CLAUDE_ACCESS_MAP_PC3_CREATOR.md`, and `contracts/claude-access-map.json`. If the checkout origin, path, runtime profile, permissions, or game target conflicts with those files, stop rather than adapting the wrong project.

Finish the active `_pizza-agent` Slice-1 housekeeping first, then execute the numbered Creator tasks in the current queue. Do not ask for, inspect, enumerate, print, or commit credential values/credential filenames; use the existing secrets/runtime credential abstraction only.

# Confirmed method-level handoff for the parallel backend

- Live target: `S:\Unity_Games\PC3 - Pizza Creator`.
- The supplied ZIP includes the exact `Assembly-CSharp.dll`, 2,681 decompiled C# files (2,093 main + 588 firstpass; 246,809 lines), 79 Managed DLLs, 331 StreamingAssets files and the runnable Unity 2017.3.1p4 x64 build. The earlier “DLL not materialized” boundary no longer applies here.
- There are 87 valid ingredients in Cheese, Fish, Fruit, Meat, Spice and Vegetable.
- `PizzaSauce`, `Ranch`, `CookedChicken` and accented `Jalapeño` are invalid IDs. Sauce is already on the dough; use exact IDs such as `Chicken`, `Bacon`, `Jalapeno`, `Tomato` and `Mozzarella`.
- Units are grams. `IngredientSize` is `Large=0`, `Medium=1`, `Small=2`; the earlier reverse mapping is wrong. Ingredient price is `Amount / 100f * BasePrice`.
- Shapes are Round, Square, Star and Triangle. Copy `IDatabaseService.GetPizzaShape(shapeId).DoughPositions`; do not impose a unit-circle schema.
- Native generated placement uses X `[-5.5,-0.5]`, Z `[-2.5,2.5]`, Y layers near `1.0 + n×0.01`, with rotation around Y.
- A valid runtime model is built by binding `PizzaModel`, adding selected dough positions, binding each `IngredientContainerModel`, assigning the real size-specific `IngredientModel`, position and rotation, then setting ID and ProfitFactor.
- `IPizzaCreatorService.LoadPizzaFromModel(PizzaModel)` is public and is the correct Apply bridge. It resets the pizza, starts placement, invokes the game's internal `PlaceIngredient` for every container, restores name/profit and publishes `PizzaLoaded`.
- Cost and price come from the bound `PizzaModel`. Real score inputs come from every `CitizenTypeController` via `RatePizzaRecipe`, `RatePizzaOverallTaste` and `RatePizzaPriceTaste`.
- `TabBar.RegisterTab(Tab)` is public. A BepInEx 5 runtime tab is safer than replacing the game's assembly.
- The real 3D composer is the renderer. A flat generated texture is optional and must not replace ingredient placement.
- The unified AI tab owns Chat, Lab, Crew and Voice. The Python sidecar is provider-agnostic, offline-capable and not authoritative over IDs/cost/native scores.
- The package now includes `assets/barros-pizza-creator-header.png`; the runtime hides `Bakehouse` only on the AI tab, aspect-fits this mark into the title strip, leaves the stock close button clear, and restores the original label on other tabs.
- The exact-game plugin now compiles with zero errors and is shipped as `artifacts/Barros.PizzaCreator.AI.dll` (66,560 bytes; SHA-256 `63e18cce15e3faede1a18f9f32ec73768a2053f89fe29a8ca95240ebabab5501`). `artifacts/build-provenance.json` locks every compiler reference and source hash.
- `contracts/rc1.acceptance.json` and `scripts/Invoke-ProofContract.ps1` are the source of truth for status. No runtime gate may be inferred from source or mockups.
- F8 captures the canonical live screenshot for the active mode. After stock recipe-book reload, F9 compares the real `PizzaModel` with the saved snapshot and records `action.reload.verified` only on an exact modeled match.
- `docs/ENGINEERING_PLAYBOOK.md` is the complete reproducible notebook; `docs/PROJECT_STATUS.md` is the factual gate snapshot. Current combined evidence is 7 pass, 1 Windows-only blocked, 16 not run and 0 fail out of 24 gates.
- User-owned audio is now staged at `S:\Unity_Games\PC3 - Pizza Creator\Barros_Music`. `CONVERT_BARROS_MUSIC.bat` produces decode-validated Ogg Vorbis files and per-file hashes without shipping or inventing music. Automatic scene playback remains intentionally separate until the live audio mixer route is observed.

Please align any Slice 1 interchange schema to these facts before the UI consumes it.
