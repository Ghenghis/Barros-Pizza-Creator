from __future__ import annotations

import hashlib
import json
import math
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from typing import Any

from .ingredient_intelligence import ingredient_profile, ingredient_set_cohesion, suggest_pairings
from .inspiration import InspirationLibrary
from .models import AgentOpinion, Recipe, RecipeIngredient, RecipeScores
from .providers import ProviderClient, ProviderError, extract_json
from .solver import CatalogIndex, repair_recipe


AGENTS: tuple[tuple[str, str], ...] = (
    ("Flavor Chef", "Suggest bold, coherent flavor combinations and protect taste."),
    ("Cost Manager", "Keep ingredient cost efficient and protect the requested price target."),
    ("Customer Scout", "Predict broad appeal, current preferences, and audience fit."),
    ("Creative Director", "Create a memorable name, visual identity, and original arrangement."),
)

THEMES: tuple[dict[str, Any], ...] = (
    {
        "name": "Desert Fire",
        "keywords": ("arizona", "southwest", "spicy", "hot", "desert", "bold"),
        "ingredients": ("Mozzarella", "Chicken", "Bacon", "Jalapeno", "Pepper", "Onion", "Chili"),
        "summary": "Smoky, savory and brightly spicy with a Southwest finish.",
        "rationale": "Chicken and bacon supply a rich base while jalapeno, pepper and chili deliver layered heat.",
    },
    {
        "name": "Casa Grande Supreme",
        "keywords": ("crowd", "favorite", "balanced", "supreme", "family", "popular"),
        "ingredients": ("Mozzarella", "Salami", "Mushroom", "Pepper", "Onion", "Olive", "Oregano"),
        "summary": "A familiar, colorful supreme tuned for broad appeal.",
        "rationale": "Classic meat, vegetables and oregano cover the major flavor families without overloading cost.",
    },
    {
        "name": "Copper State BBQ",
        "keywords": ("bbq", "barbecue", "smoky", "meat", "brisket", "profit"),
        "ingredients": ("Gouda", "Beef", "Bacon", "Onion", "Pepper", "Garlic", "Chili"),
        "summary": "A smoky meat-forward pizza with sweet onion and a warm chile edge.",
        "rationale": "Beef and bacon make the signature while gouda, onion and garlic add depth with restrained portions.",
    },
    {
        "name": "Garden Sunburst",
        "keywords": ("vegetarian", "veggie", "garden", "fresh", "green", "healthy"),
        "ingredients": ("Mozzarella", "Tomato", "Mushroom", "Spinach", "Pepper", "Onion", "Basil"),
        "summary": "A vivid vegetable pizza with a basil-led, garden-fresh profile.",
        "rationale": "Colorful vegetables provide variety while mozzarella and basil keep the flavor familiar.",
    },
    {
        "name": "Aegean Market",
        "keywords": ("mediterranean", "greek", "coastal", "olive", "feta"),
        "ingredients": ("Feta", "Tomato", "Olive", "Onion", "Pepper", "Spinach", "Oregano"),
        "summary": "Briny, herbal and vegetable-forward with a Mediterranean character.",
        "rationale": "Feta and olive bring salinity while tomato, spinach and oregano keep every bite bright.",
    },
    {
        "name": "Island Ember",
        "keywords": ("hawaiian", "pineapple", "island", "tropical", "sweet"),
        "ingredients": ("Mozzarella", "Ham", "Pineapple", "Jalapeno", "Onion", "Bacon"),
        "summary": "Sweet tropical fruit, savory ham and an optional jalapeno spark.",
        "rationale": "Pineapple balances cured meat while onion and jalapeno stop the profile becoming too sweet.",
    },
    {
        "name": "Midnight Truffle",
        "keywords": ("mushroom", "fungi", "earthy", "gourmet", "luxury"),
        "ingredients": ("Gorgonzola", "Mushroom", "Porcino", "Onion", "Garlic", "Thyme"),
        "summary": "An earthy, aromatic pizza with a rich blue-cheese accent.",
        "rationale": "Two mushroom varieties build depth while thyme, garlic and gorgonzola provide a restaurant-style finish.",
    },
    {
        "name": "Green Machine",
        "keywords": ("vegan", "plant", "dairy-free", "meatless"),
        "ingredients": ("VeganCheese", "VeganSausage", "Spinach", "Broccoli", "Pepper", "Onion", "Basil"),
        "summary": "A generous plant-based pizza with green vegetables and savory vegan sausage.",
        "rationale": "Vegan cheese and sausage provide comfort-food weight while fresh vegetables keep it lively.",
    },
)

EXCLUSION_PATTERNS = {
    "vegetarian": {"Meat", "Fish"},
    "vegan": {"Meat", "Fish", "Cheese"},
    "dairy-free": {"Cheese"},
    "dairy free": {"Cheese"},
    "no meat": {"Meat"},
    "no fish": {"Fish"},
}


def _seed(prompt: str, explicit: Any = None) -> int:
    if explicit not in (None, ""):
        try:
            return int(explicit) & 0x7FFFFFFF
        except (TypeError, ValueError):
            pass
    return int(hashlib.sha256((prompt or "surprise").encode("utf-8")).hexdigest()[:8], 16)


def _catalog_for_prompt(catalog: CatalogIndex) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in catalog.ingredients:
        result.append(
            {
                "id": item.id,
                "family": item.type_id,
                "craziness": round(item.craziness, 3),
                "profile": ingredient_profile(item),
                "sizes": [{"size": size.size, "grams": size.grams} for size in item.sizes],
            }
        )
    return result


def _pick_theme(prompt: str, rng: random.Random, offset: int = 0) -> dict[str, Any]:
    lowered = prompt.casefold()
    scored = []
    for theme in THEMES:
        score = sum(2 for keyword in theme["keywords"] if keyword in lowered)
        scored.append((score, rng.random(), theme))
    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    if scored and scored[0][0] > 0:
        return scored[offset % min(3, len(scored))][2]
    return THEMES[(rng.randrange(len(THEMES)) + offset) % len(THEMES)]


def _excluded_families(prompt: str) -> set[str]:
    lowered = prompt.casefold()
    result: set[str] = set()
    for phrase, families in EXCLUSION_PATTERNS.items():
        if phrase in lowered:
            result.update(families)
    return result


def _requested_ingredients(prompt: str, catalog: CatalogIndex) -> list[str]:
    lowered = " " + re.sub(r"[^a-z0-9]+", " ", prompt.casefold()) + " "
    hits: list[tuple[int, str]] = []
    for item in catalog.ingredients:
        candidates = {item.id.casefold(), item.name.casefold()}
        for candidate in candidates:
            normalized = re.sub(r"[^a-z0-9]+", " ", candidate).strip()
            if normalized and (" " + normalized + " ") in lowered:
                hits.append((lowered.index(" " + normalized + " "), item.id))
                break
    return [item_id for _, item_id in sorted(hits)]


def _offline_recipe(
    prompt: str,
    catalog: CatalogIndex,
    seed: int,
    variant: int,
    constraints: dict[str, Any],
) -> Recipe:
    rng = random.Random(seed + variant * 7919)
    theme = _pick_theme(prompt, rng, variant)
    excluded = _excluded_families(prompt)
    explicit = _requested_ingredients(prompt, catalog)
    intelligent_pairings = suggest_pairings(explicit, catalog.ingredients, limit=4) if explicit else []
    requested = explicit + intelligent_pairings + list(theme["ingredients"])
    unique: list[str] = []
    for ingredient_id in requested:
        item, _ = catalog.resolve(ingredient_id)
        if not item or item.type_id in excluded or item.id in unique:
            continue
        unique.append(item.id)

    max_count = max(2, min(int(constraints.get("max_ingredients", 8) or 8), 12))
    unique = unique[:max_count]
    heat = str(constraints.get("heat", "") or "").casefold()
    if heat in {"medium", "hot"} and "Jalapeno" not in unique:
        jalapeno, _ = catalog.resolve("Jalapeno")
        if jalapeno and jalapeno.type_id not in excluded:
            unique.append(jalapeno.id)
    if heat == "hot" and "Chili" not in unique:
        chili, _ = catalog.resolve("Chili")
        if chili and chili.type_id not in excluded:
            unique.append(chili.id)
    unique = unique[:max_count]

    ingredients: list[RecipeIngredient] = []
    distributions = ("even", "random", "ring", "artistic", "spiral")
    for index, ingredient_id in enumerate(unique):
        item, _ = catalog.resolve(ingredient_id)
        if not item:
            continue
        size_name = "Medium"
        if index == 0 and item.type_id == "Cheese":
            size_name = "Large"
        elif item.type_id == "Spice":
            size_name = "Small"
        size = item.size(size_name)
        target = size.grams * (5 if size_name == "Large" else (8 if size_name == "Medium" else 12))
        if "low cost" in prompt.casefold() or "cheap" in prompt.casefold() or "profit" in prompt.casefold():
            target *= 0.75
        ingredients.append(
            RecipeIngredient(
                id=item.id,
                size=size.size,
                target_grams=round(target, 2),
                distribution=distributions[(index + variant) % len(distributions)],
            )
        )

    adjective = ("Signature", "Grand", "Fire-Roasted")[variant % 3]
    name = theme["name"] if variant == 0 else adjective + " " + theme["name"]
    recipe = Recipe(
        name=name,
        summary=theme["summary"],
        shape=str(constraints.get("shape", "Round") or "Round"),
        profit_factor=float(constraints.get("profit_factor", 0.6) or 0.6),
        ingredients=ingredients,
        rationale=theme["rationale"],
        seed=seed + variant,
    )
    return repair_recipe(recipe, catalog)


def _estimate(recipe: Recipe, catalog: CatalogIndex) -> None:
    families: set[str] = set()
    craziness = 0.0
    estimated_cost = 0.0
    for source in recipe.ingredients:
        item, _ = catalog.resolve(source.id)
        if not item:
            continue
        families.add(item.type_id)
        size = item.size(source.size)
        pieces = max(1.0, source.target_grams / max(0.01, size.grams))
        estimated_cost += pieces * size.cost
        craziness += item.craziness
    count = max(1, len(recipe.ingredients))
    family_balance = min(1.0, len(families) / 5.0)
    resolved_ingredients = [item for source in recipe.ingredients if (item := catalog.resolve(source.id)[0])]
    cohesion = ingredient_set_cohesion(resolved_ingredients)
    variety_penalty = max(0.0, (count - 9) * 2.5)
    taste = 58 + family_balance * 20 + cohesion * 20 - variety_penalty + min(4, count * 0.4)
    novelty = 52 + min(38, craziness / count * 28 + max(0, count - 4) * 3)
    originality = 50 + min(42, len({item.distribution for item in recipe.ingredients}) * 5 + craziness / count * 24)
    price = estimated_cost * (1.0 + recipe.profit_factor)
    profit = 100.0 * ((price - estimated_cost) / price) if price > 0 else 0.0
    popularity = 0.64 * taste + 0.26 * max(20, 100 - estimated_cost * 3.5) + cohesion * 10
    recipe.scores = RecipeScores(
        taste=round(max(0, min(100, taste)), 1),
        cost=round(estimated_cost, 2),
        profit=round(max(0, min(100, profit)), 1),
        popularity=round(max(0, min(100, popularity)), 1),
        novelty=round(max(0, min(100, novelty)), 1),
        originality=round(max(0, min(100, originality)), 1),
        source="backend-estimate+ingredient-intelligence-v1; game recalculates taste/cost/popularity",
    )


def _piece_cost(recipe_ingredient: RecipeIngredient, catalog: CatalogIndex) -> tuple[float, float]:
    item, _ = catalog.resolve(recipe_ingredient.id)
    if not item:
        return 0.0, 1.0
    size = item.size(recipe_ingredient.size)
    pieces = max(1.0, recipe_ingredient.target_grams / max(0.01, size.grams))
    return size.cost * pieces, max(0.01, size.grams)


def _enforce_request_constraints(
    recipe: Recipe, constraints: dict[str, Any], catalog: CatalogIndex, prompt: str = ""
) -> Recipe:
    excluded_values = constraints.get("exclude") or []
    if isinstance(excluded_values, str):
        excluded_values = [part.strip() for part in excluded_values.split(",")]
    excluded_ids: set[str] = set()
    excluded_types: set[str] = {value.casefold() for value in _excluded_families(prompt)}
    for value in excluded_values:
        text_value = str(value).strip()
        resolved, _ = catalog.resolve(text_value)
        if resolved:
            excluded_ids.add(resolved.id.casefold())
        if text_value.casefold() in catalog.by_type:
            excluded_types.add(text_value.casefold())
    if excluded_ids or excluded_types:
        kept = []
        for ingredient in recipe.ingredients:
            item, _ = catalog.resolve(ingredient.id)
            if item and (item.id.casefold() in excluded_ids or item.type_id.casefold() in excluded_types):
                recipe.warnings.append("Excluded ingredient removed: " + item.id)
            else:
                kept.append(ingredient)
        recipe.ingredients = kept

    max_count = max(2, min(int(constraints.get("max_ingredients", 8) or 8), 12))
    if len(recipe.ingredients) > max_count:
        recipe.ingredients = recipe.ingredients[:max_count]
        recipe.warnings.append("Limited recipe to the requested %d ingredients." % max_count)

    ceiling = float(constraints.get("price_ceiling", 0) or 0)
    if ceiling > 0 and recipe.ingredients:
        maximum_cost = ceiling / max(1.0, 1.0 + recipe.profit_factor)
        for _ in range(500):
            costs = [(_piece_cost(ingredient, catalog)[0], index) for index, ingredient in enumerate(recipe.ingredients)]
            total = sum(value for value, _ in costs)
            if total <= maximum_cost + 0.001:
                break
            _, index = max(costs)
            target = recipe.ingredients[index]
            _, grams_per_piece = _piece_cost(target, catalog)
            if target.target_grams <= grams_per_piece + 0.001:
                if len(recipe.ingredients) <= 2:
                    break
                recipe.warnings.append("Removed %s to meet the price ceiling." % target.id)
                recipe.ingredients.pop(index)
            else:
                target.target_grams = round(max(grams_per_piece, target.target_grams - grams_per_piece), 2)
        if sum(_piece_cost(item, catalog)[0] for item in recipe.ingredients) > maximum_cost + 0.01:
            recipe.warnings.append("The requested price ceiling could not be guaranteed with two ingredients.")

    recipe = repair_recipe(recipe, catalog)
    if excluded_ids or excluded_types:
        filtered: list[RecipeIngredient] = []
        for ingredient in recipe.ingredients:
            resolved, _ = catalog.resolve(ingredient.id)
            if (
                resolved
                and resolved.id.casefold() not in excluded_ids
                and resolved.type_id.casefold() not in excluded_types
            ):
                filtered.append(ingredient)
        recipe.ingredients = filtered
        seen = {ingredient.id.casefold() for ingredient in recipe.ingredients}
        for candidate in catalog.ingredients:
            if len(recipe.ingredients) >= 2:
                break
            if (
                candidate.id.casefold() in seen
                or candidate.id.casefold() in excluded_ids
                or candidate.type_id.casefold() in excluded_types
            ):
                continue
            size = candidate.size("Medium")
            recipe.ingredients.append(
                RecipeIngredient(
                    id=candidate.id,
                    size=size.size,
                    target_grams=round(size.grams * 4.0, 2),
                    distribution="even",
                )
            )
            seen.add(candidate.id.casefold())
    return recipe


class PizzaOrchestrator:
    def __init__(self, provider: ProviderClient, inspiration: InspirationLibrary | None = None):
        self.provider = provider
        self.inspiration = inspiration

    def compose(self, payload: dict[str, Any], count: int = 1) -> dict[str, Any]:
        prompt = str(payload.get("prompt", "") or "Surprise me with a memorable pizza.").strip()
        current_pizza = str(payload.get("current_pizza", "") or "").strip()
        planning_prompt = prompt
        if current_pizza and "improve" in prompt.casefold():
            planning_prompt += "\nUse this current pizza as the starting point: " + current_pizza
        constraints = payload.get("constraints") if isinstance(payload.get("constraints"), dict) else {}
        catalog = CatalogIndex.from_payload(payload.get("catalog") or [])
        if not catalog.ingredients:
            raise ValueError("The game ingredient catalog was empty.")
        count = max(1, min(int(payload.get("count", count) or count), 3))
        seed = _seed(planning_prompt, payload.get("seed"))
        attachments = list(payload.get("attachments") or [])
        inspiration_used: list[dict[str, Any]] = []
        if bool(payload.get("use_inspiration_library")) and self.inspiration is not None:
            library_attachments, inspiration_used = self.inspiration.attachments_for_prompt(planning_prompt)
            attachments.extend(library_attachments)
        recipes: list[Recipe]
        warning = ""
        provider_completed_with_inspiration = False
        if self.provider.online:
            try:
                recipes = self._online_compose(
                    planning_prompt, constraints, catalog, count, seed, attachments
                )
                provider_completed_with_inspiration = bool(inspiration_used)
            except (ProviderError, ValueError, KeyError, TypeError) as exc:
                warning = "Online provider failed; used the built-in designer: %s" % exc
                recipes = [_offline_recipe(planning_prompt, catalog, seed, i, constraints) for i in range(count)]
        else:
            recipes = [_offline_recipe(planning_prompt, catalog, seed, i, constraints) for i in range(count)]
        for recipe in recipes:
            _enforce_request_constraints(recipe, constraints, catalog, prompt)
            _estimate(recipe, catalog)
            if warning:
                recipe.warnings.append(warning)
        message = "I designed %d game-valid pizza%s." % (len(recipes), "" if len(recipes) == 1 else "s")
        if provider_completed_with_inspiration:
            message += " I sent %d local inspiration image%s with the completed provider request." % (
                len(inspiration_used), "" if len(inspiration_used) == 1 else "s"
            )
        elif inspiration_used:
            message += " I selected local inspiration, but visual analysis needs an online vision provider."
        return {
            "ok": True,
            "message": message,
            "provider": self.provider.settings.provider,
            "recipes": [recipe.to_dict() for recipe in recipes],
            "warnings": [warning] if warning else [],
            "inspiration": inspiration_used,
            "inspiration_sent_to_provider": provider_completed_with_inspiration,
            "inspiration_analyzed": None if provider_completed_with_inspiration else False,
        }

    def _online_compose(
        self,
        prompt: str,
        constraints: dict[str, Any],
        catalog: CatalogIndex,
        count: int,
        seed: int,
        attachments: list[dict[str, Any]],
    ) -> list[Recipe]:
        system = (
            "You design recipes for the standalone Pizza Connection 3 Pizza Creator. "
            "Use ONLY catalog IDs. Sauce and dough are already present and are not ingredients. "
            "Use each catalog item's compact flavor, dietary and allergen profile to prefer coherent pairings. "
            "Amounts are grams, and size must be Large, Medium, or Small. Return strict JSON only: "
            '{"recipes":[{"name":"...","summary":"...","shape":"Round|Square|Star|Triangle",'
            '"profit_factor":0.6,"ingredients":[{"id":"exact ID","size":"Medium",'
            '"target_grams":80,"distribution":"even|center|ring|edge|random|spiral|artistic"}],'
            '"rationale":"..."}]}. Create exactly %d alternatives.' % count
        )
        attachment_notes = []
        for attachment in attachments:
            if not isinstance(attachment, dict):
                continue
            name = str(attachment.get("name", "attachment"))
            text_value = str(attachment.get("text", ""))[:12000]
            if text_value:
                attachment_notes.append({"name": name, "text": text_value})
            elif attachment.get("data_base64"):
                attachment_notes.append({"name": name, "image": "attached for visual analysis"})
        user = json.dumps(
            {
                "request": prompt,
                "constraints": constraints,
                "seed": seed,
                "catalog": _catalog_for_prompt(catalog),
                "attachments": attachment_notes,
            },
            ensure_ascii=False,
        )
        parsed = extract_json(self.provider.complete_multimodal(system, user, attachments))
        raw_recipes = parsed.get("recipes") if isinstance(parsed, dict) else parsed
        if not isinstance(raw_recipes, list) or not raw_recipes:
            raise ValueError("Provider returned no recipe alternatives.")
        result: list[Recipe] = []
        for index, raw in enumerate(raw_recipes[:count]):
            if not isinstance(raw, dict):
                continue
            raw["seed"] = seed + index
            result.append(repair_recipe(Recipe.from_dict(raw), catalog))
        if not result:
            raise ValueError("Provider recipes were not valid objects.")
        while len(result) < count:
            result.append(_offline_recipe(prompt, catalog, seed, len(result), constraints))
        return result

    def crew(self, payload: dict[str, Any]) -> dict[str, Any]:
        composed = self.compose({**payload, "count": 1}, count=1)
        recipe = Recipe.from_dict(composed["recipes"][0])
        if self.provider.online:
            opinions = self._online_crew(str(payload.get("prompt", "")), recipe)
        else:
            opinions = self._offline_crew(recipe)
        consensus = round(sum(opinion.score for opinion in opinions) / max(1, len(opinions)), 1)
        return {
            **composed,
            "message": "The four-person design crew reached %.0f%% consensus." % consensus,
            "agents": [opinion.to_dict() for opinion in opinions],
            "consensus": {
                "name": recipe.name,
                "score": consensus,
                "flavor": recipe.scores.taste,
                "profit": recipe.scores.profit,
                "popularity": recipe.scores.popularity,
                "originality": recipe.scores.originality,
            },
        }

    def _offline_crew(self, recipe: Recipe) -> list[AgentOpinion]:
        return [
            AgentOpinion("Flavor Chef", AGENTS[0][1], "%s has a coherent, craveable flavor arc." % recipe.name, recipe.scores.taste),
            AgentOpinion("Cost Manager", AGENTS[1][1], "The %.0f%% margin is workable; portions remain adjustable in-game." % recipe.scores.profit, max(0, min(100, 100 - recipe.scores.cost * 2.5))),
            AgentOpinion("Customer Scout", AGENTS[2][1], "The ingredient mix should read clearly to a broad audience.", recipe.scores.popularity),
            AgentOpinion("Creative Director", AGENTS[3][1], "The name and placement pattern give this pizza a recognizable signature.", recipe.scores.originality),
        ]

    def _online_crew(self, prompt: str, recipe: Recipe) -> list[AgentOpinion]:
        system_base = "You are one member of a four-person pizza design crew. Be concrete and concise. Return JSON {\"message\":\"...\",\"score\":0-100}."
        recipe_json = json.dumps(recipe.to_dict(), ensure_ascii=False)

        def ask(agent: str, role: str) -> AgentOpinion:
            raw = self.provider.complete(system_base + " You are %s. %s" % (agent, role), "Request: %s\nDraft: %s" % (prompt, recipe_json), 0.4)
            parsed = extract_json(raw)
            return AgentOpinion(agent, role, str(parsed.get("message", "Ready."))[:280], float(parsed.get("score", 75)))

        opinions: dict[str, AgentOpinion] = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(ask, agent, role): (agent, role) for agent, role in AGENTS}
            for future in as_completed(futures):
                agent, role = futures[future]
                try:
                    opinions[agent] = future.result()
                except Exception as exc:  # one persona must not break the crew
                    opinions[agent] = AgentOpinion(agent, role, "Unavailable: %s" % exc, 50, "warning")
        return [opinions[agent] for agent, _ in AGENTS]
