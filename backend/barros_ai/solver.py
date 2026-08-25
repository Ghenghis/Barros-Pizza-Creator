from __future__ import annotations

import math
import re
from collections.abc import Iterable

from .models import (
    CatalogIngredient,
    Recipe,
    RecipeIngredient,
    VALID_SHAPES,
    normalize_size,
)


ALIASES = {
    "jalapeño": "Jalapeno",
    "jalapenos": "Jalapeno",
    "jalapeños": "Jalapeno",
    "bellpepper": "Pepper",
    "bell pepper": "Pepper",
    "rocket": "Rucola",
    "rocket salad": "Rucola",
    "arugula": "Rucola",
    "mushrooms": "Mushroom",
    "mushroom": "Mushroom",
    "porcini": "Porcino",
    "cookedchicken": "Chicken",
    "cooked chicken": "Chicken",
    "groundbeef": "Minced",
    "ground beef": "Minced",
    "redonion": "Onion",
    "red onion": "Onion",
    "vegan sausage": "VeganSausage",
    "vegan cheese": "VeganCheese",
    "chickpea": "Chickpeas",
    "kidney beans": "Kidneybeans",
    "green beans": "GreenBeans",
}

INVALID_NON_INGREDIENTS = {
    "pizzasauce",
    "pizza sauce",
    "tomato sauce",
    "ranch",
    "ranch drizzle",
    "chipotle sauce",
    "crust",
    "dough",
}

VALID_DISTRIBUTIONS = {"even", "center", "ring", "edge", "random", "spiral", "artistic"}


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _levenshtein(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    previous = list(range(len(right) + 1))
    for index, char_left in enumerate(left, start=1):
        current = [index]
        for j, char_right in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[j] + 1,
                    previous[j - 1] + (char_left != char_right),
                )
            )
        previous = current
    return previous[-1]


class CatalogIndex:
    def __init__(self, ingredients: Iterable[CatalogIngredient]):
        self.ingredients = [item for item in ingredients if item.id]
        self.by_id = {_key(item.id): item for item in self.ingredients}
        self.by_name = {_key(item.name): item for item in self.ingredients}
        self.by_type: dict[str, list[CatalogIngredient]] = {}
        for item in self.ingredients:
            self.by_type.setdefault(item.type_id.casefold(), []).append(item)

    @classmethod
    def from_payload(cls, values: list[dict]) -> "CatalogIndex":
        return cls(CatalogIngredient.from_dict(value) for value in values)

    def resolve(self, requested: str) -> tuple[CatalogIngredient | None, str]:
        text = str(requested or "").strip()
        normalized = _key(text)
        if normalized in {_key(value) for value in INVALID_NON_INGREDIENTS}:
            return None, ""
        alias = ALIASES.get(text.casefold())
        if alias:
            item = self.by_id.get(_key(alias)) or self.by_name.get(_key(alias))
            return item, text if item and _key(item.id) != normalized else ""
        direct = self.by_id.get(normalized) or self.by_name.get(normalized)
        if direct:
            return direct, ""
        if not normalized or not self.ingredients:
            return None, ""
        choices = self.ingredients
        best = min(
            choices,
            key=lambda item: min(_levenshtein(normalized, _key(item.id)), _levenshtein(normalized, _key(item.name))),
        )
        distance = min(_levenshtein(normalized, _key(best.id)), _levenshtein(normalized, _key(best.name)))
        threshold = max(2, int(math.ceil(len(normalized) * 0.34)))
        return (best, text) if distance <= threshold else (None, "")

    def choose(self, type_id: str, preferred: tuple[str, ...] = ()) -> CatalogIngredient | None:
        for value in preferred:
            item, _ = self.resolve(value)
            if item:
                return item
        family = self.by_type.get(type_id.casefold(), [])
        return family[0] if family else (self.ingredients[0] if self.ingredients else None)


def repair_recipe(recipe: Recipe, catalog: CatalogIndex) -> Recipe:
    recipe.name = (recipe.name or "AI Pizza").strip()[:60]
    recipe.summary = (recipe.summary or "A game-valid AI-designed pizza.").strip()[:280]
    recipe.rationale = (recipe.rationale or recipe.summary).strip()[:500]
    recipe.shape = next(
        (shape for shape in VALID_SHAPES if shape.casefold() == recipe.shape.casefold()),
        "Round",
    )
    recipe.profit_factor = max(0.0, min(float(recipe.profit_factor or 0.6), 2.0))

    repaired: list[RecipeIngredient] = []
    seen: set[str] = set()
    for source in recipe.ingredients:
        item, repaired_from = catalog.resolve(source.id)
        if item is None:
            if source.id:
                recipe.warnings.append("Removed unknown ingredient: " + source.id)
            continue
        if item.id.casefold() in seen:
            existing = next(value for value in repaired if value.id.casefold() == item.id.casefold())
            existing.target_grams += max(0.0, source.target_grams)
            continue
        seen.add(item.id.casefold())
        size_name = normalize_size(source.size)
        size = item.size(size_name)
        grams = float(source.target_grams or 0)
        if grams <= 0:
            grams = size.grams * 8.0
        grams = max(size.grams, min(grams, size.grams * 24.0))
        distribution = source.distribution if source.distribution in VALID_DISTRIBUTIONS else "even"
        repaired.append(
            RecipeIngredient(
                id=item.id,
                size=size.size,
                target_grams=round(grams, 2),
                distribution=distribution,
                note=source.note[:120],
                repaired_from=repaired_from,
            )
        )
        if repaired_from:
            recipe.warnings.append("Repaired ingredient '%s' to '%s'." % (repaired_from, item.id))
        if len(repaired) >= 12:
            recipe.warnings.append("Limited recipe to 12 unique ingredients.")
            break

    if len(repaired) < 2:
        for family, preferred in (
            ("Cheese", ("Mozzarella", "Gouda")),
            ("Vegetable", ("Tomato", "Onion")),
        ):
            item = catalog.choose(family, preferred)
            if item and item.id.casefold() not in seen:
                size = item.size("Medium")
                repaired.append(
                    RecipeIngredient(
                        id=item.id,
                        size=size.size,
                        target_grams=round(size.grams * 8.0, 2),
                    )
                )
                seen.add(item.id.casefold())

    recipe.ingredients = repaired
    return recipe

