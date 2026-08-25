from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


VALID_SIZES = ("Large", "Medium", "Small")
VALID_SHAPES = ("Round", "Square", "Star", "Triangle")


def normalize_size(value: Any) -> str:
    text = str(value or "Medium").strip().lower()
    for size in VALID_SIZES:
        if text == size.lower():
            return size
    return "Medium"


@dataclass(slots=True)
class CatalogSize:
    size: str
    grams: float
    cost: float

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "CatalogSize":
        return cls(
            size=normalize_size(value.get("size")),
            grams=float(value.get("grams", value.get("amount", 0)) or 0),
            cost=float(value.get("cost", value.get("price", 0)) or 0),
        )


@dataclass(slots=True)
class CatalogIngredient:
    id: str
    name: str
    type_id: str
    craziness: float = 0.0
    sizes: list[CatalogSize] = field(default_factory=list)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "CatalogIngredient":
        ingredient_id = str(value.get("id", value.get("ID", ""))).strip()
        return cls(
            id=ingredient_id,
            name=str(value.get("name", ingredient_id)).strip() or ingredient_id,
            type_id=str(value.get("type_id", value.get("TypeID", "Unknown"))).strip(),
            craziness=float(value.get("craziness", value.get("Craziness", 0)) or 0),
            sizes=[CatalogSize.from_dict(item) for item in value.get("sizes", [])],
        )

    def size(self, requested: str) -> CatalogSize:
        normalized = normalize_size(requested)
        for item in self.sizes:
            if item.size == normalized:
                return item
        if self.sizes:
            return min(self.sizes, key=lambda item: abs(item.grams - 40.0))
        return CatalogSize(normalized, 10.0, 0.0)


@dataclass(slots=True)
class RecipeIngredient:
    id: str
    size: str = "Medium"
    target_grams: float = 0.0
    distribution: str = "even"
    note: str = ""
    repaired_from: str = ""

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "RecipeIngredient":
        return cls(
            id=str(value.get("id", value.get("ID", ""))).strip(),
            size=normalize_size(value.get("size")),
            target_grams=float(
                value.get("target_grams", value.get("grams", value.get("amount", 0))) or 0
            ),
            distribution=str(value.get("distribution", "even")).strip().lower(),
            note=str(value.get("note", "")).strip(),
        )


@dataclass(slots=True)
class RecipeScores:
    taste: float = 0.0
    cost: float = 0.0
    profit: float = 0.0
    popularity: float = 0.0
    novelty: float = 0.0
    originality: float = 0.0
    source: str = "backend-estimate"


@dataclass(slots=True)
class Recipe:
    name: str
    summary: str
    shape: str = "Round"
    profit_factor: float = 0.6
    ingredients: list[RecipeIngredient] = field(default_factory=list)
    scores: RecipeScores = field(default_factory=RecipeScores)
    rationale: str = ""
    warnings: list[str] = field(default_factory=list)
    seed: int = 0

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Recipe":
        raw_scores = value.get("scores") or {}
        return cls(
            name=str(value.get("name", "AI Pizza")).strip(),
            summary=str(value.get("summary", "")).strip(),
            shape=str(value.get("shape", value.get("dough", {}).get("shape", "Round"))).strip(),
            profit_factor=float(
                value.get("profit_factor", value.get("profit", value.get("markup", 0.6))) or 0.6
            ),
            ingredients=[RecipeIngredient.from_dict(item) for item in value.get("ingredients", [])],
            scores=RecipeScores(
                taste=float(raw_scores.get("taste", 0) or 0),
                cost=float(raw_scores.get("cost", 0) or 0),
                profit=float(raw_scores.get("profit", 0) or 0),
                popularity=float(raw_scores.get("popularity", 0) or 0),
                novelty=float(raw_scores.get("novelty", 0) or 0),
                originality=float(raw_scores.get("originality", 0) or 0),
                source=str(raw_scores.get("source", "backend-estimate")),
            ),
            rationale=str(value.get("rationale", value.get("why_it_works", ""))).strip(),
            warnings=[str(item) for item in value.get("warnings", [])],
            seed=int(value.get("seed", 0) or 0),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AgentOpinion:
    agent: str
    role: str
    message: str
    score: float
    status: str = "ready"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

