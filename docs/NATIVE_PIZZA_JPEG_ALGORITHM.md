# PC3 Pizza Creator native JPG and editable-recipe contract

Scope: **Pizza Connection 3 Pizza Creator only** (`creator-0.11.272`, Windows x64, Unity `2017.3.1p4`). Earlier game versions are excluded.

Status: source-proven on 2026-08-27 from private repository `Ghenghis/PC3_Pizza-Creator`, commit `d8fdd733fa068e00048441375a69feb8fd5b5440`. Live Windows output still requires runtime acceptance; the implementation path is no longer unknown.

## Result

The stock Pizza Creator has two independent outputs:

1. A normal JPG screenshot for sharing.
2. A serialized `PizzaModel` JSON recipe for editing and reloading.

The JPG does **not** contain the editable recipe, ingredient placements, encrypted game data, or a custom metadata payload. The game writes the bytes returned by Unity's JPG encoder directly to disk. There is no native JPG-to-`PizzaModel` importer.

Therefore:

- JPG files are visual references and exports.
- Recipe JSON is the editable source of truth.
- Importing an arbitrary pizza photo or JPG is an AI reconstruction task, not a lossless native round trip.
- Every AI-created pizza must retain a validated recipe/placement manifest separately from its preview or exported JPG.

The machine-readable form of this result is `contracts/pc3-creator-native-jpeg.contract.json`.

## Exact stock JPG pipeline

| Property | Source-proven value |
|---|---|
| UI entry | `UserInterface.ScreenshotButton` |
| Live model name | `Commands.GetCurrentPizzaCommand` → `PizzaModel.ID` |
| Filename cleaning | Invalid Windows filename characters removed; trailing period removed |
| Capture component | global `ScreenCapture` class |
| Capture camera | serialized `ScreenCapture.captureCam` reference |
| Source render size | 2560 × 1440 |
| Scale | 0.5 |
| Final texture size | 1280 × 720 |
| Camera aspect | 16:9 |
| Render target depth | 24 bits |
| Readback format | `TextureFormat.RGB24` |
| Readback | `Texture2D.ReadPixels` |
| Resize | `CaptureUtility.Resize` via GPU render target and `Graphics.DrawTexture` |
| Encoder | `Texture2D.EncodeToJPG` |
| Encoder quality | 90 |
| Output directory | `Application.streamingAssetsPath/Screenshots` |
| Output naming | `<sanitized pizza name>_<N>.jpg` |
| Retention | Five files per pizza name; the oldest path is reused at the limit |
| File write | `File.WriteAllBytes` with encoder bytes |
| Custom APP/COM insertion | None in application code |
| Embedded recipe payload | None |

The source call graph is:

```text
ScreenshotButton click
  -> GetCurrentPizzaCommand
  -> sanitize PizzaModel.ID
  -> ScreenCapture.Capture(name)
  -> CaptureUtility.Capture(camera, 2560, 1440, 0.5)
  -> Camera.Render + ReadPixels + GPU resize
  -> CaptureUtility.SaveAsJPG(..., quality 90, max files 5)
  -> Texture2D.EncodeToJPG(90)
  -> File.WriteAllBytes(.../StreamingAssets/Screenshots/name_N.jpg)
```

`ShareButton`, `BrowseScreenshotsButton`, and `SendByMail` reuse this screenshot path. The standalone `SocialAPIServiceImpl` methods are unimplemented and throw `NotImplementedException`; they are not needed for local JPG export.

## Exact editable recipe pipeline

The editable pizza is `PizzaModel`, not the JPG.

`PizzaCreatorServiceImpl.SaveToRecipes`:

1. Finds or creates the recipe model by `PizzaModel.ID`.
2. Copies the live current pizza.
3. Refreshes dough coordinates from live `PizzaDoughPart` objects.
4. Temporarily removes full ingredient object references while retaining ingredient identity fields.
5. Serializes the model through `ISerializerService.Serialize`.
6. Writes `<PizzaModel.ID>.json` under `Application.persistentDataPath/UserData/Recipes`.
7. Restores runtime ingredient references and publishes `SavedToRecipes`.

Top-level serialized fields:

- `ID`
- `Ingredients`
- `DoughPositions`
- `ProfitFactor`
- `Owner`
- `Texture`

Each ingredient placement carries:

- `Ingredient`
- `IngredientID`
- `Rotation`
- `Position`
- `Size`

The mod uses the native `IPizzaCreatorService.LoadPizzaFromModel(PizzaModel)` path for Preview, Apply, Restore, and the final reload step. F9 first reads the persisted recipe JSON, deserializes it with PC3's injected `ISerializerService`, binds each placement, resolves every `IngredientID`/size through `IDatabaseService`, and then calls the native loader. That loader resets the live dough, instantiates real `PlacedIngredient` prefabs at the supplied transforms, applies the name/profit factor, and publishes `PizzaLoaded`.

## Native thumbnail versus shared JPG

The game also has `PizzaTexture.CaptureCamera`, which reacts to `CurrentPizzaSaved` and creates a transparent sprite for the saved model. `PizzaModel` serializes that texture as PNG bytes in its `Texture` member. This thumbnail path is separate from the 1280 × 720 shared JPG path.

Do not treat the PNG thumbnail, recipe JSON, and shared JPG as interchangeable artifacts.

## AI integration contract

The simplest reliable workflow is:

```text
User prompt / voice / reference images
  -> local Workbench-compatible AI sidecar
  -> exact 87-ingredient catalog validation
  -> shape + ingredient-size + placement recipe
  -> native PizzaModel
  -> LoadPizzaFromModel preview/apply
  -> SaveCurrentPizzaToRecipes JSON
  -> stock ScreenCapture JPG export
  -> collection index with recipe hash + JPG perceptual hash
```

The provider may propose a design, but it never writes free-form values directly into the game. The local bridge validates:

- ingredient ID exists in the exact installed database;
- size is `Large`, `Medium`, or `Small`;
- shape is `Round`, `Square`, `Star`, or `Triangle`;
- name is safe for the native recipe/JPG filename paths;
- placement count and numeric transforms are bounded;
- save JSON exists and is non-empty after native save;
- exported bytes are a complete JPG stream;
- reloaded model signature matches the saved native recipe.

Reference JPGs may be inspected by a vision-capable provider and compared by perceptual hash. The resulting pizza remains a new validated reconstruction. A sidecar collection record should bind:

- recipe JSON path and hash;
- exported JPG path and hash;
- normalized perceptual hash;
- source/reference hashes;
- provider/model and prompt receipt;
- runtime profile and plugin version;
- native save/reload proof receipt.

## Research retired by this source

The following former unknowns are closed and must not be reopened without contradictory runtime evidence:

- final JPG API/library;
- encoder quality;
- source and output dimensions;
- camera render/readback path;
- output directory and rotation limit;
- whether recipe data is encrypted or embedded in the JPG;
- whether a JPG alone can recreate an editable pizza;
- whether recipe save and JPG export are the same operation.

The old hidden-payload/codec hypothesis is rejected by the exact source. Existing controlled-image comparison tooling may still be used to measure camera framing, visual placement, occlusion, repeatability, or perceptual similarity, but it is not a recipe-codec recovery program.

## Remaining live Windows gates

Source proof does not substitute for real execution. Before promotion from RC:

1. Build the plugin against the installed `Assembly-CSharp.dll`, Unity modules, Zenject, and BepInEx.
2. Verify the fifth AI tab loads in the actual `PizzaCreator` scene.
3. Preview and apply a recipe for all four shapes.
4. Save and verify the persisted native recipe JSON.
5. Use F9 to deserialize the persisted JSON through PC3's serializer, rebind its ingredients, invoke native reload, and compare the full model signature.
6. Export through the scene-local stock `ScreenshotButton`/`ScreenCapture` pair, verify its screenshot-only UI is restored, and verify a 1280 × 720 quality-90 JPG is written.
7. Confirm the five-file rotation behavior using six exports of one pizza name.
8. Relaunch the Creator and load the saved recipe through the stock recipe book.
9. Capture retained screenshots, logs, hashes, and uninstall/restore evidence through Runtime Proof Studio/HermesProof.

## Source evidence

| Source file | Git blob SHA |
|---|---|
| `pizza-creator/Assembly-CSharp/ScreenCapture.cs` | `93e87273de5cd88606eb61d583d932d6e100328c` |
| `pizza-creator/Assembly-CSharp/Service.Serializer/ISerializerService.cs` | `7311939db803c50e23b620d9e2ffb3cf1dd89e79` |
| `pizza-creator/Assembly-CSharp/CaptureUtility.cs` | `edf089f298c6ad231b0eab14c87aeb8a20d1e37b` |
| `pizza-creator/Assembly-CSharp/UserInterface/ScreenshotButton.cs` | `8db11919f2d649b9c50dd4b78f6a8624ce8400b8` |
| `pizza-creator/Assembly-CSharp/PizzaModel.cs` | `811db365510ad159f296acf7af9fbfa547bc87d8` |
| `pizza-creator/Assembly-CSharp/Service.PizzaCreator/PizzaCreatorServiceImpl.cs` | `af08b2d0ef8e8a9926c539ddfc792ee001283426` |
| `pizza-creator/Assembly-CSharp/Service.PizzaCreator/IPizzaCreatorService.cs` | `79729f7923c65518c577e617f45fb8c1105b63a7` |
| `pizza-creator/Assembly-CSharp/Service.Database/IDatabaseService.cs` | `7bdc506bab7646b336d6f11779129ed1975642b7` |
| `pizza-creator/Assembly-CSharp/Paths.cs` | `ceabf2b6b7f0241d5f4c7851d5c41258dcd3cd3d` |

The private decompiled-source repository remains evidence material and must not be copied into this public release repository or packaged with the mod.
