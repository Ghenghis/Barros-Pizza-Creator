from __future__ import annotations

from itertools import combinations
from typing import Iterable

from .models import CatalogIngredient


FAMILY_TRAITS: dict[str, dict[str, tuple[str, ...]]] = {
    "Cheese": {
        "flavor": ("creamy", "savory", "rich"),
        "dietary": ("vegetarian",),
        "allergens": ("milk",),
    },
    "Fish": {
        "flavor": ("briny", "savory", "umami"),
        "dietary": ("pescatarian",),
        "allergens": ("fish",),
    },
    "Fruit": {
        "flavor": ("sweet", "bright", "juicy"),
        "dietary": ("vegetarian", "vegan"),
        "allergens": (),
    },
    "Meat": {
        "flavor": ("savory", "rich", "umami"),
        "dietary": (),
        "allergens": (),
    },
    "Spice": {
        "flavor": ("aromatic", "bright", "seasoned"),
        "dietary": ("vegetarian", "vegan"),
        "allergens": (),
    },
    "Vegetable": {
        "flavor": ("fresh", "savory", "garden"),
        "dietary": ("vegetarian", "vegan"),
        "allergens": (),
    },
}


PROFILE_OVERRIDES: dict[str, dict[str, tuple[str, ...]]] = {
    "Mozzarella": {"flavor": ("mild", "creamy", "melty")},
    "Gorgonzola": {"flavor": ("bold", "tangy", "funky")},
    "Parmesan": {"flavor": ("nutty", "salty", "umami")},
    "Feta": {"flavor": ("tangy", "briny", "crumbly")},
    "VeganCheese": {"dietary": ("vegetarian", "vegan"), "allergens": ()},
    "Anchovy": {"flavor": ("salty", "briny", "umami")},
    "Salmon": {"flavor": ("rich", "buttery", "savory")},
    "Shrimp": {"flavor": ("sweet", "briny", "delicate"), "allergens": ("shellfish",)},
    "Crab": {"allergens": ("shellfish",)},
    "Lobster": {"allergens": ("shellfish",)},
    "BlueMussel": {"allergens": ("shellfish",)},
    "Cockle": {"allergens": ("shellfish",)},
    "Squid": {"allergens": ("shellfish",)},
    "Pineapple": {"flavor": ("sweet", "tangy", "tropical")},
    "Fig": {"flavor": ("honeyed", "jammy", "earthy")},
    "Pear": {"flavor": ("sweet", "delicate", "floral")},
    "Avocado": {"flavor": ("creamy", "mild", "fresh")},
    "Pepperoni": {"flavor": ("spiced", "salty", "savory")},
    "Chorizo": {"flavor": ("smoky", "spicy", "savory")},
    "Bacon": {"flavor": ("smoky", "salty", "rich")},
    "Chicken": {"flavor": ("mild", "savory", "lean")},
    "VeganSausage": {"dietary": ("vegetarian", "vegan"), "flavor": ("savory", "spiced")},
    "Tofu": {"dietary": ("vegetarian", "vegan"), "allergens": ("soy",), "flavor": ("mild", "savory")},
    "Egg": {"dietary": ("vegetarian",), "allergens": ("egg",), "flavor": ("rich", "silky")},
    "Garlic": {"flavor": ("pungent", "aromatic", "savory")},
    "Basil": {"flavor": ("fresh", "peppery", "aromatic")},
    "Jalapeno": {"flavor": ("green", "spicy", "bright")},
    "Chili": {"flavor": ("hot", "fruity", "spicy")},
    "Tomato": {"flavor": ("tangy", "juicy", "umami")},
    "Olive": {"flavor": ("briny", "fruity", "savory")},
    "Onion": {"flavor": ("sweet", "pungent", "savory")},
    "Mushroom": {"flavor": ("earthy", "umami", "savory")},
    "Porcino": {"flavor": ("woodsy", "earthy", "umami")},
    "Rucola": {"flavor": ("peppery", "fresh", "green")},
    "Seaweed": {"flavor": ("briny", "mineral", "umami")},
}


DISPLAY_NAMES = {
    "BelPaese": "Bel Paese",
    "RacletteCheese": "Raclette cheese",
    "BlueMussel": "Blue mussel",
    "Rasberry": "Raspberry",
    "VeganSausage": "Vegan sausage",
    "Kidneybeans": "Kidney beans",
    "GreenBeans": "Green beans",
    "Peasecod": "Pea pods",
    "Porcino": "Porcini mushroom",
}


PAIRINGS: dict[frozenset[str], float] = {
    frozenset(("Mozzarella", "Basil")): 1.0,
    frozenset(("Mozzarella", "Tomato")): 1.0,
    frozenset(("Parmesan", "Mushroom")): 0.9,
    frozenset(("Gorgonzola", "Pear")): 1.0,
    frozenset(("Gorgonzola", "Fig")): 0.95,
    frozenset(("Feta", "Olive")): 1.0,
    frozenset(("Feta", "Spinach")): 0.9,
    frozenset(("Chicken", "Jalapeno")): 0.9,
    frozenset(("Chicken", "Garlic")): 0.9,
    frozenset(("Chicken", "Bacon")): 0.7,
    frozenset(("Pepperoni", "Mushroom")): 0.85,
    frozenset(("Pepperoni", "Onion")): 0.75,
    frozenset(("Chorizo", "Pepper")): 0.9,
    frozenset(("Chorizo", "Onion")): 0.85,
    frozenset(("Ham", "Pineapple")): 1.0,
    frozenset(("Bacon", "Pineapple")): 0.75,
    frozenset(("Anchovy", "Olive")): 0.9,
    frozenset(("Salmon", "Rucola")): 0.85,
    frozenset(("Shrimp", "Garlic")): 1.0,
    frozenset(("Mushroom", "Thyme")): 1.0,
    frozenset(("Mushroom", "Garlic")): 0.9,
    frozenset(("Tomato", "Basil")): 1.0,
    frozenset(("Tomato", "Oregano")): 0.9,
    frozenset(("Avocado", "Jalapeno")): 0.85,
    frozenset(("VeganSausage", "Pepper")): 0.85,
    frozenset(("Tofu", "Ginger")): 0.9,
}


def ingredient_profile(item: CatalogIngredient) -> dict[str, object]:
    family = FAMILY_TRAITS.get(item.type_id, {"flavor": ("savory",), "dietary": (), "allergens": ()})
    override = PROFILE_OVERRIDES.get(item.id, {})
    return {
        "display_name": DISPLAY_NAMES.get(item.id, item.name or item.id),
        "flavor": list(override.get("flavor", family["flavor"]))[:4],
        "dietary": list(override.get("dietary", family["dietary"])),
        "allergens": list(override.get("allergens", family["allergens"])),
    }


def pairing_strength(left: str, right: str) -> float:
    if left == right:
        return 0.0
    return PAIRINGS.get(frozenset((left, right)), 0.0)


def suggest_pairings(
    anchor_ids: Iterable[str],
    catalog: Iterable[CatalogIngredient],
    limit: int = 4,
) -> list[str]:
    anchors = tuple(dict.fromkeys(anchor_ids))
    anchor_set = set(anchors)
    catalog_items = list(catalog)
    anchor_families = {source.type_id for source in catalog_items if source.id in anchor_set}
    candidates: list[tuple[float, float, str]] = []
    for item in catalog_items:
        if item.id in anchor_set:
            continue
        direct = max((pairing_strength(anchor, item.id) for anchor in anchors), default=0.0)
        family_bonus = 0.0
        if anchors:
            family_bonus = 0.12 if item.type_id not in anchor_families else 0.0
        candidates.append((direct + family_bonus, -item.craziness, item.id))
    candidates.sort(reverse=True)
    return [item_id for score, _, item_id in candidates if score > 0.0][: max(0, limit)]


def ingredient_set_cohesion(ingredients: Iterable[CatalogIngredient]) -> float:
    values = list(ingredients)
    if len(values) < 2:
        return 0.5
    pair_scores = [pairing_strength(left.id, right.id) for left, right in combinations(values, 2)]
    positive = sum(pair_scores)
    families = len({item.type_id for item in values})
    diversity = min(1.0, families / 4.0)
    known_pairing = min(1.0, positive / max(1.0, len(values) * 0.55))
    fruit_overload = max(0, sum(item.type_id == "Fruit" for item in values) - 2) * 0.08
    return max(0.0, min(1.0, 0.35 + diversity * 0.30 + known_pairing * 0.35 - fruit_overload))
