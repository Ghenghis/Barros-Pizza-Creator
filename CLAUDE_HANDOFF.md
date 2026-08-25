# SCOPE: PC3 PIZZA CREATOR ONLY — Claude Handoff

> **Repository:** `Ghenghis/Barros-Pizza-Creator`  
> **Owner:** Claude  
> **Runtime profile:** `creator-0.11.272`  
> **Windows product root:** `S:\Unity_Games\PC3 - Pizza Creator`  
> **Isolated workspace:** `S:\Unity_Games\PC3 - Pizza Creator\_agent-workspaces\claude-pc3-creator`  
> **Current execution queue:** `CLAUDE_NEXT_TASKS_PC3_CREATOR.md`  
> **Skip-ahead implementation packet:** `docs/CLAUDE_SKIP_AHEAD_RUNTIME_IMPLEMENTATION_PACKET.md`  
> **Method/file implementation atlas:** `docs/CLAUDE_METHOD_FILE_IMPLEMENTATION_ATLAS.md`  
> **Native JPEG reverse-engineering roadmap:** `docs/NATIVE_PIZZA_JPEG_REVERSE_ENGINEERING_ROADMAP.md`  
> **Research-backed algorithms/JPEG guide:** `docs/RESEARCH_BACKED_PLACEMENT_AND_JPEG_GUIDE.md`  
> **Current placement algorithm reference:** `docs/CURRENT_PIZZA_PLACEMENT_ALGORITHM_REFERENCE.md`  
> **JPEG research truth contract:** `contracts/jpeg-reverse-engineering.acceptance.json`  
> **Machine-readable JPEG experiments:** `contracts/jpeg-experiment-plan.json`  
> **Shared controlled stimulus schema:** `contracts/creator-controlled-stimulus.schema.json`  
> **Studio stimulus corpus generator (READ-ONLY integration):** `Ghenghis/PC3_Barros_Runtime_Proof_Studio/scripts/generate_creator_controlled_stimuli.py`  
> **Studio controlled observer (READ-ONLY integration):** `Ghenghis/PC3_Barros_Runtime_Proof_Studio/CAPTURE_CREATOR_CONTROLLED_JPEG_EXPERIMENT.bat`  
> **JPEG tooling setup:** `docs/JPEG_RE_TOOLING_SETUP.md` + `DOWNLOAD_JPEG_RESEARCH_TOOLS.bat`  
> **Native JPEG pair analyzer:** `ANALYZE_NATIVE_JPEG_PAIR.bat` + `scripts/analyze_jpeg_experiment.py`  
> **Machine-readable queue:** `contracts/claude-creator-task-queue.json`  
> **Complete access/location map:** `CLAUDE_ACCESS_MAP_PC3_CREATOR.md`  
> **Machine-readable access map:** `contracts/claude-access-map.json`  
> **Verified shared Google Drive root ID:** `1v_EZAxzNZQbi5DjpwWxBTiMyPHaIut34`  
> **Ownership:** Claude owns PC3 Pizza Creator. ChatGPT owns Runtime Proof Studio, Barro's Workbench, and the main PC3 ecosystem. Studio/Workbench/main-PC3 locations are READ-ONLY integration references for Claude unless the user explicitly changes ownership.  
> **Forbidden:** work outside the locked PC3 program scope unless the user explicitly changes scope.

## Access rule — read this before doing any work

Claude has a complete map of the known local, Google Drive, GitHub, GitLab, Creator-sidecar, and Windows-MCP locations in `CLAUDE_ACCESS_MAP_PC3_CREATOR.md` and `contracts/claude-access-map.json`.

A documented location is **not** proof that Claude Desktop is authenticated to it. At the beginning of a session, verify access without exposing credentials. Use these access modes exactly:

- **WRITE:** PC3 Pizza Creator local product root, `_pizza-agent`, isolated Claude Creator workspace, Creator GitHub repository, and Creator-specific Drive folders only when the task explicitly requires a Drive write.
- **READ-ONLY / INTEGRATION:** Runtime Proof Studio, Barro's Workbench, main PC3 local roots, main PC3 Google Drive folders, extraction outputs, shared contracts, and ecosystem evidence.
- **VERIFY FIRST:** Google Drive authentication in Claude Desktop, GitHub push authentication, configured GitLab remote/authentication, and Windows-MCP reachability.
- **DENIED:** any subtree or project excluded by `PC3_ONLY_SCOPE.md` / `contracts/pc3-only-scope.json`.

The verified shared Google Drive root contains separate Creator and main-PC3 folders. Use the exact folder IDs in the access map. Never infer that a similarly named Drive folder is the same target. The access map also contains a denied Drive subtree ID so an agent cannot accidentally traverse outside the locked PC3 program scope.

For GitLab, use only `SYNC_GITLAB_SAFE.bat` / `scripts/Sync-GitLabSafe.ps1`. The remote name is normally `gitlab`, but the URL is intentionally not guessed or committed. Fetch first, verify ancestry, never force-push, and verify the remote SHA after a normal push.

Before editing, read `00_READ_FIRST_PC3_ONLY.md`, `PC3_ONLY_SCOPE.md`, `WORKSTREAM_OWNERSHIP.md`, `contracts/pc3-only-scope.json`, `contracts/workstream-ownership.json`, `CLAUDE_ACCESS_MAP_PC3_CREATOR.md`, `contracts/claude-access-map.json`, `docs/CLAUDE_SKIP_AHEAD_RUNTIME_IMPLEMENTATION_PACKET.md`, and `docs/CLAUDE_METHOD_FILE_IMPLEMENTATION_ATLAS.md`. If the checkout origin, path, runtime profile, permissions, or game target conflicts with those files, stop rather than adapting the wrong project.

Finish the active `_pizza-agent` Slice-1 housekeeping first, then execute the numbered Creator tasks in the current queue. Use the skip-ahead implementation packet and method/file atlas to avoid repeating settled architecture research. Do not ask for, inspect, enumerate, print, or commit credential values/credential filenames; use the existing secrets/runtime credential abstraction only.

## Parallel research lane — native pizza JPEG/image generation

The native pizza-image/JPEG generation algorithm must be reverse engineered rather than guessed.

Canonical research files:

- `docs/NATIVE_PIZZA_JPEG_REVERSE_ENGINEERING_ROADMAP.md`
- `docs/RESEARCH_BACKED_PLACEMENT_AND_JPEG_GUIDE.md`
- `docs/CURRENT_PIZZA_PLACEMENT_ALGORITHM_REFERENCE.md`
- `docs/JPEG_RE_TOOLING_SETUP.md`
- `contracts/jpeg-reverse-engineering.acceptance.json`
- `contracts/jpeg-experiment-plan.json`
- `contracts/creator-controlled-stimulus.schema.json`

Executable lab entry points:

- `DOWNLOAD_JPEG_RESEARCH_TOOLS.bat` — stages pinned official ILSpy/dnSpyEx/AssetRipper/libjpeg-turbo downloads with SHA-256 validation, builds an isolated image-analysis Python environment, and offers optional RenderDoc/ImageMagick installation.
- `ANALYZE_NATIVE_JPEG_PAIR.bat` — GUI file-picker wrapper for A/B native JPEG comparisons.
- `scripts/analyze_jpeg_experiment.py` — hashes files, parses SOF/DQT/DHT/APP/COM/restart/scan structure, and adds decoded pixel metrics/diff/SSIM when optional dependencies are present.
- `tests/test_jpeg_experiment_analyzer.py` — standard-library regression coverage using embedded known JPEG samples.

This lane is **parallel research**, not permission to abandon the core Creator runtime gates. Static work (`JRE-001`, `JRE-002`, and any source-resolvable portions of the render path) may run as soon as Slice-1 housekeeping is stable. Live JPEG experiments should reuse the exact Creator runtime/save/reload work already required by the main queue instead of creating a competing test harness.

### Research-only controlled fixture executor

Implement `CLD-JPEG-FIXTURE-EXECUTOR` in the Creator workstream. Its only purpose is to remove human placement error from the controlled experiment corpus.

Contract:

- accept only `creator-0.11.272` fixtures conforming to `contracts/creator-controlled-stimulus.schema.json`;
- the shared schema in Creator and Runtime Proof Studio must remain semantically identical;
- the Studio-owned generator produces explicit E00-E10 test fixtures; Claude may consume its output but must not edit Studio/Workbench implementation;
- bind a `PizzaModel` directly from the fixture's exact shape/name/profit factor/ingredient IDs/sizes/positions/rotations;
- obtain dough positions from `IDatabaseService.GetPizzaShape(shape).DoughPositions` and size-specific ingredients from `IDatabaseService`;
- **do not call the Barro's/golden-angle placement generator for fixture execution** because the fixture already supplies every transform;
- load the exact fixture through `IPizzaCreatorService.LoadPizzaFromModel(PizzaModel)`;
- if `native_recipe_save` is requested, call `IPizzaCreatorService.SaveCurrentPizzaToRecipes()`; do not generate, encode, rewrite, patch, or post-process the JPEG in the executor;
- if reload verification is requested, reload through the stock/native recipe-book path, require exact `ModelSignature` agreement, then invoke the same stock save path again when `native_resave_after_reload` is true;
- retain experiment ID, case ID, exact input fixture hash, model signature, runtime profile, timestamps, and native action success/failure events;
- never convert successful fixture loading into a JRE PASS by itself. Runtime Proof Studio independently retains UserData before/after state and analyzes the native output.

This creates the intended two-party proof chain:

`Studio explicit fixture -> Claude Creator exact model/native save -> stock Creator UserData/JPEG -> Studio independent before/after/hash/pixel/DQT/DHT/DCT/transform analysis`.

The controlled experiment program must include:

- identical model saved repeatedly for determinism;
- one-piece rotation sweep;
- X-axis and Z-axis world-to-image mapping sweeps;
- Y/layer overlap tests;
- same ingredient set with rotations changed only;
- same ingredient set with positions changed only;
- reversed ingredient list order with transforms held constant;
- piece-count sweep;
- Large/Medium/Small comparison;
- Round/Square/Star/Triangle comparison;
- native Save -> native reload -> exact model verification -> JPEG re-save comparison.

For every important A/B pair, retain exact model signature plus JPEG SHA-256 and quantitative image metrics. The roadmap calls for raw JPEG structure, RMSE/PSNR, SSIM, difference bounds and PHASH where available rather than visual judgment alone.

The research target is to identify the actual native chain from save/model through camera/render target/draw order/crop/scale/colorspace/JPEG encoder. Classify every discovered component as `PROVEN_FROM_SOURCE`, `PROVEN_FROM_RUNTIME`, `INFERRED_AND_VALIDATED`, or `UNKNOWN`.

The research-backed enhanced-placement candidate is intentionally separate from native matching. The literature-backed route combines a deterministic golden-angle initializer, variable/anisotropic Poisson separation, sample elimination to preserve exact piece count, bounded capacity/Lloyd-style density relaxation, ingredient-aware orientation, exact native transforms, and the native renderer. Do not switch the default to this enhanced algorithm until stock/native behavior is characterized and the user can choose native-match vs enhanced behavior.

Do not improve the stock image algorithm until it is characterized. After characterization, prefer in this order:

1. exact reuse of the native image generator;
2. native renderer with a controlled deterministic capture path;
3. independent reimplementation only if native reuse/capture is impossible.

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
- User-owned audio is staged under the Creator product root in `Barros_Music`. `CONVERT_BARROS_MUSIC.bat` produces decode-validated Ogg Vorbis files and per-file hashes without shipping or inventing music. Automatic scene playback remains intentionally separate until the live audio mixer route is observed.

Please align any Slice 1 interchange schema to these facts before the UI consumes it.
