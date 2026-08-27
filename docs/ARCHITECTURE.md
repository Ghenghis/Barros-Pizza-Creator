# Architecture and verified game bridge

## Runtime layers

| Layer | Location | Responsibility |
|---|---|---|
| Runtime tab | BepInEx plugin | Adds one registered Pizza Creator tab without replacing game assemblies |
| Four-mode panel | Unity IMGUI anchored to the cloned content rect | Chat, Lab, Crew, Voice, history, attachments, recipe cards and actions |
| Header brand | Runtime-loaded PNG under `BarrosAI/assets` | Aspect-fits the Barro's Pizza Creator mark while the AI tab is active |
| Game bridge | `GameBridge.cs` | Live catalog, model binding, positions, preview/apply/restore, persisted native recipe save, stock JPG export and native scores |
| Sidecar | `backend/` on `127.0.0.1:48173` | Provider routing, deterministic fallback, repair, orchestration and history |
| Provider | Local or hosted | OpenAI-compatible, Ollama, Anthropic, multimodal images and STT |

## Verified API path

The supplied decompiled implementation establishes the following public path:

1. `Kernel.Instance.Inject(bridge)` resolves `IPizzaCreatorService` and `IDatabaseService` through Zenject.
2. `IDatabaseService.GetAllIngredients(Medium)` enumerates all IDs; `GetIngredientByID(id, size)` supplies the exact size-specific model, amount and price.
3. The bridge binds a new `PizzaModel`, copies `PizzaShapeData.DoughPositions`, binds each `PizzaModel.IngredientContainerModel`, and assigns its actual `IngredientModel`, world position and Y rotation.
4. `IPizzaCreatorService.LoadPizzaFromModel(candidate)` resets dough and ingredients, starts placement, invokes the game's private placement path for every container, restores the name/profit factor and publishes `PizzaLoaded`.
5. The plugin reactivates the AI tab after `PizzaLoaded`, because the stock `PizzaCreatorTabBar` otherwise switches to the recipe tab.
6. Native recipe save writes the editable `PizzaModel` JSON under `Application.persistentDataPath/UserData/Recipes`; the bridge requires both the native recipe-list entry and a non-empty file.
7. JPG export resolves the scene-local stock `ScreenshotButton`, enables its screenshot-only UI, reuses the referenced `ScreenCapture` 2560×1440 → 1280×720 quality-90 path under `StreamingAssets/Screenshots`, and restores the prior UI state. The JPG contains no editable recipe payload.
8. F9 reads the persisted recipe JSON through PC3's `ISerializerService`, resolves each ingredient through `IDatabaseService`, loads it through `IPizzaCreatorService`, and compares the disk model with the resulting live model.

The original `Assembly-CSharp.dll` is read as a compile reference and never modified.

## Corrected game schema

- Ingredient sizes are `Large = 0`, `Medium = 1`, `Small = 2`.
- Units are grams per placed model, not ounces.
- Price is `Amount / 100 × BasePrice`.
- Sauce is part of the base pizza; `PizzaSauce` and `Ranch` are not catalog IDs.
- Valid shapes are Round, Square, Star and Triangle.
- Native random generation uses world X `[-5.5,-0.5]`, Z `[-2.5,2.5]`, Y layers from about `1.0` upward. The bridge uses the same center and layering convention.
- Each AI ingredient intent is expanded into actual placed pieces based on target grams divided by the size model's `Amount`, with per-ingredient and total safety limits.

## Failure containment

- Unknown IDs are removed or repaired before Unity receives the response.
- A provider failure falls back to the deterministic offline designer.
- A failing persona cannot cancel the other Crew opinions.
- Preview snapshots the current `PizzaModel`; Start over reloads it.
- The installer refuses an incomplete game folder or incompatible BepInEx major version.
- Dependency archives are pinned and SHA-256 checked.
- Uninstall targets only this plugin unless the user explicitly asks to remove shared BepInEx.
