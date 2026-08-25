# Reverse-engineering evidence and release status

This file separates facts proven from the supplied Windows archive from behavior that still requires the first live Windows run.

## Supplied-build inventory

| Item | Verified value |
|---|---:|
| ZIP entries | 3,719 |
| ZIP size | 217,559,523 bytes |
| ZIP SHA-256 | `6f667a8a1624f6d0cbe57a7c3534068004b778282d03b013e77bf5243f945b86` |
| Decompiled C# files | 2,681 |
| Decompiled C# lines | 246,809 |
| `Assembly-CSharp` sources | 2,093 files / 207,151 lines |
| `Assembly-CSharp-firstpass` sources | 588 files / 39,658 lines |
| Managed DLLs | 79 |
| StreamingAssets files | 331 |
| Unity player | 2017.3.1p4 x64 |
| Product / Steam | 0.11.272 / app 851330 |
| VersionInfo assembly tag | 1.0.6683.36665 |
| Decompiled assembly attribute | 1.0.6683.37204 |

Exact assembly evidence:

- `Assembly-CSharp.dll`: 3,189,248 bytes; SHA-256 `ebf8698df7cb4af904c98c299994705ea529efbdf1e8ccb3e7ca8cb42a1cbc1c`
- `Assembly-CSharp-firstpass.dll`: 657,920 bytes; SHA-256 `f9cbf0951fc4d4b0788c47bbe41a3820fa333d293175bbb7cb398eb4728fd284`

## Pizza Creator data proven

- 87 ingredient IDs across Cheese, Fish, Fruit, Meat, Spice and Vegetable.
- Three real size records per ingredient in enum order Large, Medium, Small.
- Four shapes: Round, Square, Star and Triangle.
- Exactly 20 dough positions per shape.
- Save/model keys `ID`, `Ingredients`, `DoughPositions` and `ProfitFactor`.
- Placement keys `Ingredient`, `IngredientID`, `Rotation`, `Position` and `Size`.
- Native placement coordinates use X `[-5.5,-0.5]`, Z `[-2.5,2.5]` and layered Y values near `1.0 + n×0.01`.

## Method-level path proven from source

The chosen mod path does not require reconstructing every system in Pizza Connection 3. These are the required surfaces and each is present in the exact supplied source:

| Requirement | Verified API or class |
|---|---|
| Resolve live game services | `Kernel.Inject`, Zenject, `IPizzaCreatorService`, `IDatabaseService` |
| Enumerate exact catalog | `GetAllIngredients`, `GetIngredientByID` |
| Select real dough | `GetPizzaShape(...).DoughPositions` |
| Build model | `PizzaModel`, `IngredientContainerModel`, `Bind`, `CalculateCosts` |
| Drive 3D renderer | `IPizzaCreatorService.LoadPizzaFromModel` → native internal `PlaceIngredient` |
| Save recipe | `SaveCurrentPizzaToRecipes` |
| Score taste/popularity | `CitizenTypeController.RatePizzaRecipe`, `RatePizzaOverallTaste`, `RatePizzaPriceTaste` |
| Add UI surface | `PizzaCreatorTabBar`, `TabBar.RegisterTab`, `TabBar.ActivateTab` |

This is complete reverse-engineering coverage for the selected integration route, not a claim that every unrelated campaign, restaurant, city, AI or rendering subsystem was reverse engineered.

## Implementation state

| Area | State | Evidence |
|---|---|---|
| Catalog extraction and schema repair | Complete | Generated catalog exactly matches all 87 supplied records |
| Offline composer and constraints | Complete | Automated tests cover validity, determinism, exclusions, price ceiling and improve context |
| Provider adapters | Complete in source | OpenAI-compatible/LM Studio, Ollama and Anthropic plus provider fallback |
| Chat / Lab / Crew / Voice UI | Complete in source | Fifth registered tab and four in-panel modes map to the supplied mockups |
| 3D Preview / Apply / Restore / Save | Complete in source | Uses the public native service path above |
| Native scores | Complete in source | Game citizen and cost models replace backend estimates in Unity |
| Barro's header branding | Complete in package | 1280×143 optimized banner plus full-resolution source; runtime aspect-fit and restoration |
| Python verification | Passed | 20 backend/contract tests, including byte-model catalog and STT request checks |
| Exact-game C# compile | Passed | Roslyn compiled a 66,560-byte PE32 AnyCPU plugin with zero errors against the supplied Managed DLLs; SHA-256 `63e18cce15e3faede1a18f9f32ec73768a2053f89fe29a8ca95240ebabab5501` |
| Windows compiler parity | Pending target run | `RUN_RC1_PROOF.bat` rebuilds against the installed DLLs with Windows `csc.exe` and retains the log |
| Live Unity scene / mic / visual fit | Pending first Windows launch | `DIAGNOSE_Barros_AI` and the acceptance checklist capture proof |

Overall status: **feature-complete release-candidate source, certified exact-assembly plugin, and installer; Windows runtime certification pending**. Windows compiler parity, BepInEx loading, tab/header geometry, Preview/Restore/Apply/Save/reload, microphone/STT, and four live comparison screenshots remain explicit gates before calling the mod fully proven.
