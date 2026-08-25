# Engineering notebook and reproduction playbook

This document records what was actually inspected, built, tested, and still requires live proof. Another developer should be able to reproduce the supported path without treating a mockup, decompiler output, or successful compilation as proof of live behavior.

## 1. Truth model

The project uses four states only: `not_run`, `pass`, `fail`, and `blocked`. `contracts/rc1.acceptance.json` is the machine-readable authority. A claim becomes `pass` only after its command runs against the stated target and retains evidence. The four UI images are hash-locked visual requirements, never runtime evidence.

The selected architecture reverse engineers only the surfaces needed by the mod. It does not claim complete reconstruction of every unrelated Pizza Connection 3 subsystem.

## 2. Inputs and immutable identity

| Input | Observed identity |
|---|---|
| Supplied Windows archive | 3,719 entries; 217,559,523 bytes; SHA-256 `6f667a8a1624f6d0cbe57a7c3534068004b778282d03b013e77bf5243f945b86` |
| Product | Pizza Connection 3 - Pizza Creator `0.11.272`; Steam app `851330` |
| Unity player | `2017.3.1p4` Windows x64 |
| Main assembly | 3,189,248 bytes; SHA-256 `ebf8698df7cb4af904c98c299994705ea529efbdf1e8ccb3e7ca8cb42a1cbc1c` |
| Firstpass assembly | 657,920 bytes; SHA-256 `f9cbf0951fc4d4b0788c47bbe41a3820fa333d293175bbb7cb398eb4728fd284` |
| Supplied decompiled tree | 2,681 C# files; 246,809 lines |
| Runtime content | 79 Managed DLLs; 331 StreamingAssets files |

Every installer/build action checks the exact assembly hashes first. An unknown game build stops before the plugin is copied.

## 3. Tool ledger

| Tool | How it was used | Reproducibility record |
|---|---|---|
| Supplied decompiled C# | Symbol discovery and control-flow confirmation. The analysis consumed the supplied tree; it does not falsely claim a fresh full decompilation was performed here. | Counts and required symbols are recorded in `docs/REVERSE_ENGINEERING_EVIDENCE.md`. |
| `rg` and filesystem inventory | Located type declarations, public service methods, data-contract members, scene/resource names, and counted source/content files. | Search targets and findings are listed below. |
| BepInEx 5.4.23.5 x64 | Non-destructive Unity/Mono plugin loader; no replacement of `Assembly-CSharp.dll`. | Official archive SHA-256 `82f9878551030f54657792c0740d9d51a09500eeae1fba21106b0c441e6732c4`. |
| Microsoft .NET SDK 8.0.424 / Roslyn | Local, non-admin certification compiler invoked through `dotnet exec csc.dll`; no SDK is shipped. | C# compiler `4.11.0-3.25569.22`; exact sources/references are locked in `artifacts/build-provenance.json`. |
| PowerShell 7.6.5 portable | Parsed and executed Windows-compatible installer/proof scripts in the analysis environment. | Archive SHA-256 `b34ab3b19acac1d3d4d0d3cfdb02acf62f457b0b6a962ff008132033f7566844`. |
| Python 3.12.10 embedded x64 | Private installed sidecar runtime; no system Python or PATH mutation. | Archive SHA-256 `4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3`. |
| Python `unittest` | Deterministic composer/provider/contract tests, including byte-level multipart STT request and educational/audio-pipeline verification. | 20 tests pass in the certified package. |
| FFmpeg with `libvorbis` | Optional real-track conversion and decode validation for the supplied `Barros_Music` directory. | `scripts/Convert-BarrosMusic.ps1` records tool version and per-file hashes; FFmpeg is not bundled. |
| GitHub Actions / GitLab CI | Repeat static tests and contract/JSON checks on public repository snapshots. | `.github/workflows/rc1-contract.yml` and `.gitlab-ci.yml`. |
| Deterministic ZIP builder | Regenerates the per-file manifest, writes a fixed-timestamp archive, verifies every member hash/CRC, and updates the release checksum. | `python tools/build_release.py` |

Downloaded third-party archives were independently hashed before their values were pinned. Proprietary game files and the local toolchain are not redistributed.

## 4. Reverse-engineering route

### 4.1 Inventory before interpretation

The analysis first established build identity, then counted Managed assemblies, StreamingAssets, decompiled files, and scene/data evidence. This prevents combining facts from incompatible releases.

Representative reproducible commands from the extracted game root:

```powershell
Get-FileHash '.\Pizza Connection 3 - Pizza Creator_Data\Managed\Assembly-CSharp.dll' -Algorithm SHA256
Get-FileHash '.\Pizza Connection 3 - Pizza Creator_Data\Managed\Assembly-CSharp-firstpass.dll' -Algorithm SHA256
(Get-ChildItem '.\_decompiled' -Recurse -Filter '*.cs').Count
(Get-ChildItem '.\Pizza Connection 3 - Pizza Creator_Data\Managed' -Filter '*.dll').Count
(Get-ChildItem '.\Pizza Connection 3 - Pizza Creator_Data\StreamingAssets' -Recurse -File).Count
```

### 4.2 Required symbol map

The following supplied source locations establish the integration route:

| Question | Source evidence |
|---|---|
| How can a fifth tab be registered? | `UserInterface/TabBar.cs` → `RegisterTab`; `UserInterface/PizzaCreatorTabBar.cs` |
| How is a pizza represented and serialized? | `PizzaModel.cs`, including `DoughPositions`, `ProfitFactor`, binding, price and cost logic |
| How are exact ingredients resolved? | `Service.Database/IDatabaseService.cs` and `DatabaseServiceImpl.cs` → `GetAllIngredients`, `GetIngredientByID` |
| How are shape positions represented? | `Service.PizzaCreator/PizzaShapeData.cs` |
| How does the real renderer receive a model? | `Service.PizzaCreator/IPizzaCreatorService.cs` and `PizzaCreatorServiceImpl.cs` → `LoadPizzaFromModel` |
| How does recipe-book saving occur? | The same service → `SaveCurrentPizzaToRecipes` |
| Which native scoring functions exist? | `CitizenTypeController.cs` → `RatePizzaRecipe`, `RatePizzaOverallTaste`, `RatePizzaPriceTaste` |
| Which components render the pizza? | `PizzaController.cs`, `PlacedIngredient.cs`, `PizzaCreator/PizzaDoughRenderer.cs` |

This public-service route removed the need for Harmony detours, save-file surgery, input automation, or replacement game assemblies.

### 4.3 Corrected assumptions

Cross-referencing data and source corrected several early generic-schema assumptions:

- The valid size enum order is `Large = 0`, `Medium = 1`, `Small = 2`.
- Ingredient amounts are game records in grams, not arbitrary ounce ranges.
- Sauce is part of the base pizza; invented IDs such as `PizzaSauce` and `Ranch` cannot be sent to the live catalog.
- Valid shapes are Round, Square, Star and Triangle, each with exactly 20 supplied dough positions.
- Placement uses world coordinates centered around X `-3`, not normalized unit-circle coordinates.
- The authoritative live cost and score path is the bound `PizzaModel` plus citizen controllers, not an LLM's numbers.

## 5. Implementation layers

| Layer | Real implementation | Main files |
|---|---|---|
| Provider-independent designer | Deterministic offline design, catalog repair, constraints, history and optional hosted/local model adapters | `backend/barros_ai/` |
| Four interaction modes | Chat, AI Lab, Design Crew and Chef Voice rendered inside one registered game tab | `plugin-src/PanelRenderer.cs` |
| Native bridge | Resolves live services, extracts the catalog, binds `PizzaModel`, calls Preview/Apply/Restore/Save and native scores | `plugin-src/GameBridge.cs` |
| Runtime tab/header | Registers the fifth tab and aspect-fits the Barro's header while preserving the close button and stock title | `plugin-src/RuntimeTabInstaller.cs` |
| Voice | Unity microphone → PCM → WAV → sidecar multipart STT → prompt | `PanelRenderer.cs`, `WavEncoder.cs`, `providers.py` |
| Evidence | Structured JSONL events, canonical screenshots and saved/reloaded model comparison | `plugin-src/EvidenceRecorder.cs` |
| Installer | Hash-gated game detection, pinned dependencies, certified prebuilt, private sidecar and reversible uninstall | root PowerShell/BAT files |

## 6. Build certification

`scripts/Build-Plugin.ps1` compiles every `plugin-src/*.cs` file against the exact installed PC3, Unity and BepInEx assemblies. The certified artifact is:

- `artifacts/Barros.PizzaCreator.AI.dll`
- 66,560 bytes
- SHA-256 `63e18cce15e3faede1a18f9f32ec73768a2053f89fe29a8ca95240ebabab5501`
- PE32 .NET/Mono AnyCPU
- zero compiler errors in the exact-assembly certification run

`artifacts/build-provenance.json` records 18 reference hashes, 11 source hashes, the source-tree hash, compiler identity, output hash, and the explicit boundary that Windows runtime loading is still a separate gate.

## 7. Visual one-for-one method

The four references are stored under `docs/mockups/` and locked by SHA-256 in the contract. `docs/UI_MOCKUP_MAPPING.md` maps each visible region and control to its implementation.

The runtime method is deliberately repeatable:

1. Populate Chat, Lab, Crew and Voice with real interactions.
2. Press F8 in each mode to write canonical `chat.png`, `lab.png`, `crew.png`, and `voice.png` captures.
3. Run `scripts/Compare-ReferenceImages.ps1`.
4. Retain normalized pixel-error, edge-overlap, and difference-image reports.
5. Manually confirm legibility, hit targets, close-button access, and header restoration.

This can measure closeness and drive iteration; it cannot honestly declare a one-for-one live match before the four captures exist.

## 8. Proof snapshot

As of the certified non-Windows run:

| State | Gates | Meaning |
|---|---:|---|
| Pass | 7 / 24 | Four source/package gates and three exact-assembly build/provenance gates |
| Blocked | 1 / 24 | Windows compiler-parity gate cannot run in the Linux analysis host |
| Not run | 16 / 24 | Loader, live geometry, native actions, real microphone/STT and live visual comparisons |
| Fail | 0 / 24 | No executed gate failed |

This is a feature-complete RC source/package with an exact-assembly certified plugin, not yet a runtime-certified final release.

## 9. Shortest path to 100% proof

Install with `INSTALL_Barros_AI_Designer.bat`, launch the Creator once, exercise the flow in `docs/RUNTIME_ACCEPTANCE.md`, and then run from the extracted RC1 package:

```powershell
powershell -ExecutionPolicy Bypass -File '.\scripts\Invoke-ProofContract.ps1' `
  -Stage All -RequireComplete `
  -GameRoot 'S:\Unity_Games\PC3 - Pizza Creator'
```

If a gate fails, fix only the earliest failing layer and rerun it. Do not tune UI against screenshots while the loader gate is failing, and do not test recipe reload until Preview/Apply/Save events are proven.

## 10. Updating for another game build

1. Preserve the old release and evidence bundle.
2. Hash the new DLLs and inventory the new tree.
3. Re-run the required-symbol searches and inspect changed methods.
4. Re-extract the catalog and shape data; diff IDs, sizes, prices, and positions.
5. Update contract target hashes only after review.
6. Compile against the new exact assemblies and regenerate provenance.
7. Run all 24 gates; never carry runtime passes across game versions.

Primary vendor/upstream sources and the decisions derived from them are retained in `docs/UPSTREAM_AUDIT.md`.

## 11. Rebuilding the release package

From the repository root:

```powershell
python .\tools\build_release.py
python .\tools\build_release.py --verify-only
```

The builder excludes runtime settings, histories, evidence runs, caches, local compiler logs, proprietary game files and the release directory itself. Only the certified DLL, README and provenance JSON are allowed from `artifacts/`. It writes `MANIFEST.sha256`, builds the ZIP with fixed timestamps, verifies all member hashes and CRCs, then writes `RELEASE_CHECKSUMS.sha256`.
