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

Please align any Slice 1 interchange schema to these facts before the UI consumes it.
