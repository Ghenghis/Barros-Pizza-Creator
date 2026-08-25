# SCOPE: PC3 PIZZA CREATOR ONLY — Current Pizza Placement Algorithm Reference

**Owner:** Claude — PC3 Pizza Creator  
**Repository:** `Ghenghis/Barros-Pizza-Creator`  
**Purpose:** freeze the currently implemented placement behavior so reverse engineering can compare it against stock/native image generation without ambiguity.

This file documents the algorithm currently implemented in `plugin-src/GameBridge.cs`. It is not a claim that the stock Pizza Creator uses this same algorithm when a human manually places ingredients.

## 1. Authority boundary

The current plugin does two different things:

1. it **constructs** a `PizzaModel` using the algorithm below;
2. it hands that model to the native game through `IPizzaCreatorService.LoadPizzaFromModel(PizzaModel)`.

The native game then creates the actual 3D ingredient objects using the supplied model transforms.

Therefore:

- placement generation below = Barro's plugin algorithm;
- 3D rendering of the resulting model = native game renderer;
- native saved JPEG algorithm = separate reverse-engineering target.

## 2. Recipe seed

`GameBridge.BuildModel()` creates:

```text
System.Random random = new System.Random(
    recipe.Seed == 0
        ? StableSeed(recipe.Name)
        : recipe.Seed
)
```

If `recipe.Seed != 0`, that seed is used directly.

Otherwise `StableSeed(name)` is:

```text
hash = 17
for each character c in name:
    hash = hash * 31 + c
return hash & 0x7fffffff
```

This means the same recipe name and same inputs produce the same pseudorandom sequence under the current implementation.

## 3. Dough shape

Allowed shape names:

```text
Round
Square
Star
Triangle
```

Unknown values normalize to `Round`.

The plugin calls:

```text
database.GetPizzaShape(shape)
```

and copies the returned native `DoughPositions` into the model.

The plugin does **not** generate a unit-circle dough shape.

## 4. Piece count from grams

For every recipe ingredient:

1. parse the requested size;
2. retrieve the real installed `IngredientModel` for ID + size;
3. require a non-null model with `Amount > 0`;
4. compute:

```text
count = round(TargetGrams / ingredient.Amount)
count = clamp(count, 1, 40)
```

There is also a global maximum:

```text
maximumPlacements = 180
```

So no generated recipe can exceed 180 placed pieces through this path.

## 5. Piece rotation

Each piece gets:

```text
Rotation = (0, random[0..360), 0)
```

Only Y rotation changes in the current generated placement algorithm.

The rotation is preserved in the native `IngredientContainerModel` and therefore becomes part of the saved/reload model signature.

## 6. Base world coordinate system

Every generated position is centered around:

```text
X center = -3.0
Z center = 0.0
```

The current native coordinate envelope observed in the exact game is approximately:

```text
X [-5.5, -0.5]
Z [-2.5, 2.5]
```

Generated Y layering is:

```text
Y = 1.0 + globalPlacementIndex * 0.01
```

This gives every successive placed piece a slightly higher Y value.

## 7. Angular sequence

For piece index `i`, the current algorithm computes:

```text
angle = i * 2.399963229728653 + random() * 0.35
```

`2.399963229728653` radians is approximately the golden angle.

So the distribution is based on a golden-angle spiral/fan pattern with a small seeded angular jitter.

## 8. Distribution modes

Let:

```text
u = random() in [0,1)
```

### even

Default mode:

```text
radius = sqrt(u) * 2.08
```

The square root produces approximately uniform area density in a circular footprint rather than uniform radius density.

### center

```text
radius = sqrt(u) * 1.15
```

This concentrates pieces in the center region.

### ring

```text
radius = 1.35 + u * 0.55
```

Radius range:

```text
[1.35, 1.90)
```

### edge

```text
radius = 1.90 + u * 0.25
```

Radius range:

```text
[1.90, 2.15)
```

### spiral

```text
radius = 0.35 + 1.75 * ((i + 1) / max(1, count))
```

This increases radius deterministically with piece index.

### artistic

```text
radius = 0.65 + 1.25 * abs(sin(angle * 2.5))
```

This creates repeating lobes/petals controlled by angular position.

## 9. Convert polar placement to world coordinates

Before shape-specific adjustment:

```text
localX = cos(angle) * radius
localZ = sin(angle) * radius
```

Then:

```text
worldX = -3.0 + localX
worldZ = localZ
worldY = 1.0 + globalIndex * 0.01
```

## 10. Square-shape adjustment

For `Square` only:

```text
localX = clamp(localX * 1.08, -2.15, 2.15)
localZ = clamp(localZ * 1.08, -2.15, 2.15)
```

No corresponding shape-specific transformation currently exists in this method for Star or Triangle; those shapes still get their native dough positions, but topping distribution uses the same polar footprint unless future logic changes it.

This is an important improvement candidate after native behavior is characterized.

## 11. Model construction order

For each piece:

```text
placed = new PizzaModel.IngredientContainerModel()
placed.Bind()
placed.Ingredient = real size-specific IngredientModel
placed.Position = generated position
placed.Rotation = generated Y rotation
model.ingredients.Add(placed)
```

`globalIndex` increases after every piece across all ingredients.

Therefore ingredient-list order affects:

- random-number consumption;
- global Y layering;
- generated piece positions/rotations of later ingredients;
- potential visible overlap/order in the native renderer.

That is why reverse-engineering tests must include reversed ingredient order while keeping all other model facts controlled.

## 12. Native cost/scoring after placement

After all placements:

```text
model.CalculateCosts()
```

Then `ScoreWithGame()` queries all available `CitizenTypeController` objects and uses native:

```text
RatePizzaRecipe(model)
RatePizzaOverallTaste(model)
RatePizzaPriceTaste(model)
```

These scores are not part of the visual placement algorithm, but they are model-dependent and should be retained when comparing recipes.

## 13. Current deterministic model signature

The existing reload verifier signs:

```text
ID/name
ProfitFactor
all DoughPositions
ingredient count/order
ingredient ID
size
position
rotation
```

This is extremely useful for the JPEG reverse-engineering program because two saved JPEGs can be associated with exact model signatures rather than descriptions like "looks like the same pizza."

## 14. Known weaknesses / improvement candidates

Do not change these until the stock/native path is measured, but record them as candidates.

### Shape-aware density

Current toppings are fundamentally circular/polar except a square clamp.

Possible improvement:

- use native dough polygon/position data to construct a density mask;
- reject positions outside the actual dough footprint;
- preserve edge margin per shape.

### Ingredient-specific placement

Current algorithm treats all ingredient geometry similarly.

Possible improvement:

- ingredient mesh footprint awareness;
- large-piece collision/overlap control;
- preferred orientation rules for strips/slices;
- density limits by ingredient type.

### Layering

Current Y is strictly increasing by 0.01 in ingredient traversal order.

Possible improvement after native depth behavior is proven:

- stable semantic layers;
- controlled overlap groups;
- deterministic z/depth ordering independent of recipe list order.

### Better distribution optimization

Possible algorithms:

- Poisson-disk sampling;
- weighted Lloyd relaxation/CVT;
- blue-noise sampling;
- constrained golden-angle placement;
- Voronoi-based separation;
- shape-mask rejection sampling;
- center/edge/ring mixtures;
- aesthetic objective optimization.

Any improved algorithm must preserve:

- valid native coordinates;
- exact ingredient ID/size/model binding;
- deterministic seed reproducibility;
- native Save/reload compatibility;
- native renderer compatibility.

## 15. Comparison requirement

When the stock/native manual or automatic placement algorithm is reverse engineered, compare it to this implementation dimension-by-dimension:

```text
seed/randomness
piece count
position distribution
shape handling
rotation
layer/depth rule
ingredient ordering
collision/overlap behavior
bounds/edge margin
save serialization
rendered JPEG impact
```

The final decision should explicitly say which behavior is:

```text
KEEP_CURRENT
MATCH_NATIVE
IMPROVE_OPTIONALLY
UNKNOWN
```
