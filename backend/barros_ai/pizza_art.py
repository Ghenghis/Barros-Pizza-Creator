from __future__ import annotations

import hashlib
import math
import random
import re
from collections import Counter
from typing import Any, Callable

from .models import (
    ArtworkMetadata,
    ArtworkPlacement,
    CatalogIngredient,
    Recipe,
    RecipeIngredient,
)
from .solver import CatalogIndex


MAX_ART_PLACEMENTS = 180
PIXEL_ROLES = {
    "R": "red",
    "W": "white",
    "K": "dark",
    "G": "green",
    "Y": "yellow",
    "O": "orange",
    "B": "brown",
    "P": "pink",
    "S": "skin",
    "U": "purple",
}


FAMILY_VISUALS: dict[str, dict[str, Any]] = {
    "Cheese": {"rgb": (238, 222, 174), "geometry": "shred", "footprint": 0.10, "orientation": "free"},
    "Fish": {"rgb": (186, 126, 112), "geometry": "strip", "footprint": 0.13, "orientation": "tangent"},
    "Fruit": {"rgb": (224, 151, 76), "geometry": "disc", "footprint": 0.12, "orientation": "free"},
    "Meat": {"rgb": (155, 72, 58), "geometry": "disc", "footprint": 0.13, "orientation": "free"},
    "Spice": {"rgb": (72, 124, 54), "geometry": "granular", "footprint": 0.07, "orientation": "free"},
    "Vegetable": {"rgb": (92, 142, 62), "geometry": "chunk", "footprint": 0.11, "orientation": "radial"},
}


VISUAL_OVERRIDES: dict[str, dict[str, Any]] = {
    "Mozzarella": {"rgb": (248, 242, 218), "geometry": "shred"},
    "Ricotta": {"rgb": (250, 247, 231), "geometry": "dollop"},
    "Feta": {"rgb": (245, 239, 213), "geometry": "chunk"},
    "VeganCheese": {"rgb": (245, 229, 174), "geometry": "shred"},
    "Gouda": {"rgb": (235, 180, 51), "geometry": "shred"},
    "Gorgonzola": {"rgb": (214, 218, 182), "geometry": "chunk"},
    "Olive": {"rgb": (42, 39, 28), "geometry": "ring", "footprint": 0.08},
    "Caviar": {"rgb": (30, 27, 25), "geometry": "granular", "footprint": 0.05},
    "Seaweed": {"rgb": (29, 66, 42), "geometry": "strip", "orientation": "tangent"},
    "Anchovy": {"rgb": (91, 87, 73), "geometry": "strip", "orientation": "tangent"},
    "Salmon": {"rgb": (235, 126, 91), "geometry": "strip", "orientation": "tangent"},
    "Shrimp": {"rgb": (242, 155, 126), "geometry": "curve", "orientation": "tangent"},
    "Tomato": {"rgb": (205, 48, 42), "geometry": "disc"},
    "Pepperoni": {"rgb": (156, 36, 30), "geometry": "disc"},
    "Salami": {"rgb": (137, 52, 45), "geometry": "disc"},
    "Chorizo": {"rgb": (174, 48, 30), "geometry": "disc"},
    "Ham": {"rgb": (231, 148, 153), "geometry": "chunk"},
    "Bacon": {"rgb": (145, 71, 47), "geometry": "strip", "orientation": "tangent"},
    "Chicken": {"rgb": (220, 177, 130), "geometry": "chunk"},
    "Tofu": {"rgb": (228, 213, 174), "geometry": "cube"},
    "Strawberry": {"rgb": (213, 44, 53), "geometry": "disc"},
    "Rasberry": {"rgb": (181, 31, 71), "geometry": "cluster"},
    "Grapes": {"rgb": (104, 54, 124), "geometry": "disc"},
    "Pineapple": {"rgb": (239, 194, 45), "geometry": "chunk"},
    "Corn": {"rgb": (246, 199, 43), "geometry": "granular", "footprint": 0.06},
    "Egg": {"rgb": (244, 194, 45), "geometry": "disc"},
    "Curry": {"rgb": (218, 157, 30), "geometry": "granular", "footprint": 0.05},
    "Carrots": {"rgb": (230, 104, 33), "geometry": "strip", "orientation": "tangent"},
    "Pepper": {"rgb": (213, 71, 38), "geometry": "strip", "orientation": "tangent"},
    "Spinach": {"rgb": (39, 112, 53), "geometry": "leaf", "orientation": "radial"},
    "Basil": {"rgb": (53, 126, 57), "geometry": "leaf", "orientation": "radial"},
    "Rucola": {"rgb": (67, 127, 55), "geometry": "leaf", "orientation": "radial"},
    "Broccoli": {"rgb": (50, 112, 49), "geometry": "cluster"},
    "Jalapeno": {"rgb": (48, 117, 50), "geometry": "ring"},
    "Mushroom": {"rgb": (167, 132, 96), "geometry": "cap"},
    "Porcino": {"rgb": (128, 91, 62), "geometry": "cap"},
    "Potato": {"rgb": (213, 183, 125), "geometry": "disc"},
    "Onion": {"rgb": (238, 224, 213), "geometry": "ring"},
    "Garlic": {"rgb": (239, 229, 196), "geometry": "chip"},
}


ROLE_CANDIDATES = {
    "red": ("Tomato", "Pepperoni", "Salami", "Chorizo", "Strawberry", "Rasberry", "Peperoni"),
    "white": ("Mozzarella", "Ricotta", "Feta", "VeganCheese", "Onion", "Garlic"),
    "dark": ("Olive", "Seaweed", "Caviar", "Anchovy", "Kidneybeans"),
    "green": ("Spinach", "Basil", "Broccoli", "Jalapeno", "Rucola", "Seaweed", "Kiwi"),
    "yellow": ("Corn", "Pineapple", "Egg", "Curry", "Starfruit", "Gouda"),
    "orange": ("Carrots", "Salmon", "Peach", "Pepper"),
    "brown": ("Mushroom", "Dates", "Bacon", "Beef", "Porcino"),
    "pink": ("Ham", "Salmon", "Strawberry", "Rasberry"),
    "skin": ("Ham", "Chicken", "Tofu", "Potato", "Mushroom", "Mozzarella"),
    "purple": ("Grapes", "Rasberry", "Kidneybeans", "Olive"),
}


ROLE_PRIORITY = {
    "dark": 100,
    "white": 82,
    "orange": 78,
    "pink": 72,
    "red": 65,
    "yellow": 60,
    "green": 56,
    "brown": 52,
    "purple": 50,
    "skin": 38,
}


def ingredient_visual_profile(item: CatalogIngredient) -> dict[str, Any]:
    base = dict(FAMILY_VISUALS.get(item.type_id, FAMILY_VISUALS["Vegetable"]))
    base.update(VISUAL_OVERRIDES.get(item.id, {}))
    red, green, blue = base["rgb"]
    luminance = round((0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255.0, 3)
    return {
        "rgb": [red, green, blue],
        "hex": "#%02X%02X%02X" % (red, green, blue),
        "luminance": luminance,
        "geometry": str(base.get("geometry", "chunk")),
        "footprint": float(base.get("footprint", 0.11)),
        "orientation": str(base.get("orientation", "free")),
    }


def is_art_request(prompt: str, artwork: ArtworkMetadata | None = None) -> bool:
    if artwork and (artwork.enabled or artwork.template or artwork.pixel_map):
        return True
    text = prompt.casefold()
    return any(
        token in text
        for token in (
            "pizza art",
            "artwork",
            "portrait",
            "picture",
            "image design",
            "mosaic",
            "face",
            "smiley",
            "heart",
            "santa",
            "snowman",
            "christmas tree",
            "tree design",
            "star design",
        )
    )


def has_explicit_builtin_template(prompt: str) -> bool:
    text = prompt.casefold()
    return any(
        token in text
        for token in (
            "santa",
            "father christmas",
            "snowman",
            "christmas tree",
            "tree design",
            "smiley",
            "happy face",
            "emoji",
            "face pizza",
            "portrait pizza",
            "heart pizza",
            "star pizza",
        )
    )


def detect_template(prompt: str, artwork: ArtworkMetadata | None = None) -> str:
    requested = (artwork.template if artwork else "").strip().casefold()
    aliases = {
        "christmas": "tree",
        "christmas-tree": "tree",
        "happy-face": "smiley",
        "portrait": "face",
        "custom": "custom",
    }
    if requested:
        requested = aliases.get(requested, requested)
        if requested in {"santa", "tree", "snowman", "smiley", "face", "heart", "star", "custom"}:
            return requested
    text = prompt.casefold()
    if "santa" in text or "father christmas" in text:
        return "santa"
    if "snowman" in text:
        return "snowman"
    if "christmas tree" in text or "tree design" in text:
        return "tree"
    if "smiley" in text or "happy face" in text or "emoji" in text:
        return "smiley"
    if "heart" in text:
        return "heart"
    if "star" in text:
        return "star"
    if "face" in text or "portrait" in text:
        return "face"
    return "smiley"


def detect_detail(prompt: str, artwork: ArtworkMetadata | None = None) -> str:
    requested = (
        artwork.detail
        if artwork and (artwork.enabled or artwork.template or artwork.pixel_map)
        else ""
    ).strip().casefold()
    if requested in {"draft", "standard", "high"}:
        return requested
    text = prompt.casefold()
    if any(token in text for token in ("high detail", "high-detail", "detailed", "intricate", "maximum detail")):
        return "high"
    if any(token in text for token in ("simple", "quick", "draft", "draft-detail", "minimal")):
        return "draft"
    if "standard-detail" in text:
        return "standard"
    return "standard"


def detect_symmetry(prompt: str, artwork: ArtworkMetadata | None = None) -> str:
    requested = (artwork.symmetry if artwork else "").strip().casefold()
    text = prompt.casefold()
    if "radial symmetry" in text or requested == "radial":
        return "radial"
    if "freeform symmetry" in text or "asymmetric" in text or requested == "freeform":
        return "freeform"
    if "mirror symmetry" in text or requested in {"mirror", "mirrored"}:
        return "mirror"
    return "template-balanced"


def _allowed_for_diet(item: CatalogIngredient, prompt: str) -> bool:
    text = prompt.casefold()
    vegan = "vegan" in text
    vegetarian = vegan or "vegetarian" in text
    if vegan:
        if item.id in {"VeganCheese", "VeganSausage", "Tofu"}:
            return True
        return item.type_id not in {"Cheese", "Fish", "Meat"}
    if vegetarian:
        if item.id in {"VeganSausage", "Tofu", "Egg"}:
            return True
        return item.type_id not in {"Fish", "Meat"}
    return True


def choose_art_palette(catalog: CatalogIndex, prompt: str) -> dict[str, str]:
    palette: dict[str, str] = {}
    for role, candidates in ROLE_CANDIDATES.items():
        chosen: CatalogIngredient | None = None
        for candidate in candidates:
            item, _ = catalog.resolve(candidate)
            if item and _allowed_for_diet(item, prompt):
                chosen = item
                break
        if chosen is None:
            chosen = next((item for item in catalog.ingredients if _allowed_for_diet(item, prompt)), None)
        if chosen:
            palette[role] = chosen.id
    return palette


def _ellipse(x: float, y: float, cx: float, cy: float, rx: float, ry: float) -> bool:
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0


def _distance_to_segment(
    x: float, y: float, x1: float, y1: float, x2: float, y2: float
) -> float:
    dx, dy = x2 - x1, y2 - y1
    length = dx * dx + dy * dy
    if length <= 1e-9:
        return math.hypot(x - x1, y - y1)
    amount = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / length))
    return math.hypot(x - (x1 + amount * dx), y - (y1 + amount * dy))


def _santa(x: float, y: float) -> tuple[str, int] | None:
    role: tuple[str, int] | None = None
    if _ellipse(x, y, 0.0, 0.02, 0.49, 0.52):
        role = ("skin", 1)
    if role and (y < -0.10 or (abs(x) > 0.33 and y < 0.15)):
        role = ("white", 2)
    hat_width = 0.13 + max(0.0, 0.76 - y) * 0.72
    if 0.34 <= y <= 0.78 and -0.60 <= x <= min(0.46, hat_width):
        role = ("red", 2)
    if 0.29 <= y <= 0.42 and abs(x) <= 0.57:
        role = ("white", 3)
    if _ellipse(x, y, -0.58, 0.74, 0.13, 0.13):
        role = ("white", 4)
    if _ellipse(x, y, -0.18, 0.12, 0.065, 0.075) or _ellipse(x, y, 0.18, 0.12, 0.065, 0.075):
        role = ("dark", 5)
    if _ellipse(x, y, 0.0, -0.01, 0.075, 0.08):
        role = ("red", 6)
    if _ellipse(x, y, -0.13, -0.105, 0.16, 0.075) or _ellipse(x, y, 0.13, -0.105, 0.16, 0.075):
        role = ("white", 6)
    if -0.12 <= x <= 0.12 and abs(y + 0.245 + 0.18 * x * x) < 0.045:
        role = ("dark", 7)
    return role


def _smiley(x: float, y: float) -> tuple[str, int] | None:
    if x * x + y * y > 0.74 * 0.74:
        return None
    role = ("yellow", 1)
    if _ellipse(x, y, -0.24, 0.22, 0.085, 0.12) or _ellipse(x, y, 0.24, 0.22, 0.085, 0.12):
        role = ("dark", 4)
    smile_radius = math.hypot(x, y - 0.05)
    if y < -0.02 and 0.39 < smile_radius < 0.48 and abs(x) < 0.46:
        role = ("dark", 5)
    if _ellipse(x, y, -0.48, -0.02, 0.09, 0.07) or _ellipse(x, y, 0.48, -0.02, 0.09, 0.07):
        role = ("red", 3)
    return role


def _face(x: float, y: float) -> tuple[str, int] | None:
    if _ellipse(x, y, 0.0, 0.0, 0.61, 0.74):
        role: tuple[str, int] | None = ("skin", 1)
    else:
        role = None
    if role and y > 0.42 + 0.16 * math.cos(x * 7.0):
        role = ("brown", 3)
    if _ellipse(x, y, -0.23, 0.18, 0.075, 0.10) or _ellipse(x, y, 0.23, 0.18, 0.075, 0.10):
        role = ("dark", 5)
    if _distance_to_segment(x, y, -0.34, 0.34, -0.13, 0.37) < 0.035:
        role = ("brown", 5)
    if _distance_to_segment(x, y, 0.13, 0.37, 0.34, 0.34) < 0.035:
        role = ("brown", 5)
    if abs(x) < 0.07 and -0.06 < y < 0.16:
        role = ("orange", 4)
    if y < -0.18 and abs(y + 0.29 + 0.25 * x * x) < 0.045 and abs(x) < 0.30:
        role = ("red", 6)
    return role


def _heart(x: float, y: float) -> tuple[str, int] | None:
    scaled_y = y + 0.05
    value = (x * x + scaled_y * scaled_y - 0.43) ** 3 - x * x * scaled_y**3
    if value > 0 or y < -0.78 or y > 0.67:
        return None
    role = ("red", 2)
    if _distance_to_segment(x, y, -0.33, 0.30, -0.18, 0.45) < 0.06:
        role = ("white", 4)
    return role


def _point_in_polygon(x: float, y: float, points: list[tuple[float, float]]) -> bool:
    inside = False
    previous = points[-1]
    for current in points:
        x1, y1 = previous
        x2, y2 = current
        if (y1 > y) != (y2 > y):
            crossing = (x2 - x1) * (y - y1) / max(1e-9, y2 - y1) + x1
            if x < crossing:
                inside = not inside
        previous = current
    return inside


def _star(x: float, y: float) -> tuple[str, int] | None:
    points: list[tuple[float, float]] = []
    for index in range(10):
        angle = math.pi / 2.0 + index * math.pi / 5.0
        radius = 0.82 if index % 2 == 0 else 0.36
        points.append((math.cos(angle) * radius, math.sin(angle) * radius))
    if not _point_in_polygon(x, y, points):
        return None
    if x * x + y * y < 0.16:
        return ("red", 3)
    return ("yellow", 2)


def _tree(x: float, y: float) -> tuple[str, int] | None:
    role: tuple[str, int] | None = None
    if -0.82 <= y <= -0.55 and abs(x) <= 0.14:
        role = ("brown", 1)
    if -0.62 <= y <= 0.58:
        width = 0.16 + (0.62 - y) * 0.48
        if abs(x) <= width:
            role = ("green", 2)
    ornaments = ((-0.30, -0.28, "red"), (0.31, -0.30, "yellow"), (0.0, -0.05, "red"), (-0.18, 0.19, "yellow"), (0.19, 0.25, "red"))
    for cx, cy, color in ornaments:
        if _ellipse(x, y, cx, cy, 0.075, 0.075):
            role = (color, 4)
    if _ellipse(x, y, 0.0, 0.69, 0.13, 0.13):
        role = ("yellow", 5)
    if role and role[0] == "green" and abs((x * 11.0 + y * 7.0) % 1.0) < 0.10:
        role = ("white", 3)
    return role


def _snowman(x: float, y: float) -> tuple[str, int] | None:
    role: tuple[str, int] | None = None
    if _ellipse(x, y, 0.0, -0.35, 0.47, 0.43) or _ellipse(x, y, 0.0, 0.24, 0.34, 0.34):
        role = ("white", 1)
    if 0.50 <= y <= 0.68 and abs(x) <= 0.36:
        role = ("dark", 3)
    if 0.40 <= y <= 0.53 and abs(x) <= 0.48:
        role = ("dark", 3)
    if _ellipse(x, y, -0.12, 0.31, 0.05, 0.06) or _ellipse(x, y, 0.12, 0.31, 0.05, 0.06):
        role = ("dark", 5)
    if _distance_to_segment(x, y, 0.0, 0.23, 0.25, 0.17) < 0.045:
        role = ("orange", 6)
    if abs(y + 0.05) < 0.075 and abs(x) < 0.42:
        role = ("red", 4)
    for cy in (-0.22, -0.40, -0.57):
        if _ellipse(x, y, 0.0, cy, 0.045, 0.045):
            role = ("dark", 5)
    return role


TEMPLATES: dict[str, Callable[[float, float], tuple[str, int] | None]] = {
    "santa": _santa,
    "smiley": _smiley,
    "face": _face,
    "heart": _heart,
    "star": _star,
    "tree": _tree,
    "snowman": _snowman,
}


def _grid_points(template: str, detail: str) -> list[dict[str, Any]]:
    resolution = {"draft": 13, "standard": 19, "high": 25}[detail]
    function = TEMPLATES.get(template, _smiley)
    points: list[dict[str, Any]] = []
    for row in range(resolution):
        y = 0.88 - row * (1.76 / max(1, resolution - 1))
        for column in range(resolution):
            x = -0.88 + column * (1.76 / max(1, resolution - 1))
            if x * x + y * y > 0.91 * 0.91:
                continue
            value = function(x, y)
            if value:
                role, layer = value
                points.append({"x": x, "y": y, "role": role, "layer": layer})
    return points


def _custom_pixel_points(rows: list[str]) -> list[dict[str, Any]]:
    cleaned = [str(row).upper()[:21] for row in rows[:21] if str(row).strip()]
    if not cleaned:
        return []
    height = len(cleaned)
    width = max(len(row) for row in cleaned)
    if width < 3 or height < 3:
        return []
    scale = 1.74 / max(width, height)
    points: list[dict[str, Any]] = []
    for row_index, row in enumerate(cleaned):
        for column, value in enumerate(row):
            role = PIXEL_ROLES.get(value)
            if not role:
                continue
            x = (column - (width - 1) / 2.0) * scale
            y = ((height - 1) / 2.0 - row_index) * scale
            if x * x + y * y <= 0.91 * 0.91:
                points.append({"x": x, "y": y, "role": role, "layer": ROLE_PRIORITY.get(role, 1) // 20})
    return points


def _stable_limit(points: list[dict[str, Any]], seed: int, maximum: int) -> list[dict[str, Any]]:
    if len(points) <= maximum:
        return points
    ranked: list[tuple[str, int, dict[str, Any]]] = []
    by_role: dict[str, list[tuple[str, int, dict[str, Any]]]] = {}
    for index, point in enumerate(points):
        key = "%d|%.5f|%.5f|%s" % (seed, point["x"], point["y"], point["role"])
        stable = hashlib.sha256(key.encode("utf-8")).hexdigest()
        row = (stable, index, point)
        ranked.append(row)
        by_role.setdefault(str(point["role"]), []).append(row)
    reserved: set[int] = set()
    reserve_per_role = 10 if maximum >= 140 else 6
    for role_rows in by_role.values():
        role_rows.sort(key=lambda item: item[0])
        reserved.update(item[1] for item in role_rows[:reserve_per_role])
    selected = [item for item in ranked if item[1] in reserved]
    remaining = [item for item in ranked if item[1] not in reserved]
    remaining.sort(key=lambda item: item[0])
    selected.extend(remaining[: max(0, maximum - len(selected))])
    return [item[2] for item in selected[:maximum]]


def _apply_symmetry(points: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    if mode == "freeform" or mode == "template-balanced":
        return points
    transformed: list[dict[str, Any]] = []
    if mode == "mirror":
        for point in points:
            if float(point["x"]) > 0.015:
                continue
            transformed.append(dict(point))
            if abs(float(point["x"])) > 0.015:
                mirrored = dict(point)
                mirrored["x"] = -float(point["x"])
                transformed.append(mirrored)
        return transformed or points
    if mode == "radial":
        sector: list[dict[str, Any]] = []
        for point in points:
            angle = math.atan2(float(point["y"]), float(point["x"]))
            if -math.pi / 3.0 <= angle < math.pi / 3.0:
                sector.append(point)
        if not sector:
            sector = points[::3]
        for point in sector:
            for turn in range(3):
                angle = turn * math.tau / 3.0
                cosine, sine = math.cos(angle), math.sin(angle)
                rotated = dict(point)
                rotated["x"] = float(point["x"]) * cosine - float(point["y"]) * sine
                rotated["y"] = float(point["x"]) * sine + float(point["y"]) * cosine
                transformed.append(rotated)
        return transformed or points
    return points


def _placement_rotation(item: CatalogIngredient, x: float, y: float, rng: random.Random) -> float:
    visual = ingredient_visual_profile(item)
    orientation = visual["orientation"]
    if orientation == "radial":
        return math.degrees(math.atan2(y, x)) - 90.0
    if orientation == "tangent":
        return math.degrees(math.atan2(y, x))
    return rng.random() * 360.0


def compile_recipe_artwork(
    recipe: Recipe,
    prompt: str,
    catalog: CatalogIndex,
    seed: int,
) -> Recipe:
    if not is_art_request(prompt, recipe.artwork):
        return recipe
    detail = detect_detail(prompt, recipe.artwork)
    template = detect_template(prompt, recipe.artwork)
    symmetry = detect_symmetry(prompt, recipe.artwork)
    source = "built-in-vector-template"
    raw_points: list[dict[str, Any]] = []
    if recipe.artwork.pixel_map:
        raw_points = _custom_pixel_points(recipe.artwork.pixel_map)
        if raw_points:
            template = "custom"
            source = "provider-pixel-map"
    if not raw_points:
        raw_points = _grid_points(template, detail)
    raw_points = _apply_symmetry(raw_points, symmetry)
    maximum = {"draft": 96, "standard": 144, "high": 176}[detail]
    raw_points = _stable_limit(raw_points, seed, min(maximum, MAX_ART_PLACEMENTS))
    palette = choose_art_palette(catalog, prompt)
    rng = random.Random(seed ^ 0x5A17)
    organic = any(token in prompt.casefold() for token in ("organic", "handmade", "natural"))
    placements: list[ArtworkPlacement] = []
    for point in sorted(raw_points, key=lambda value: (value["layer"], value["y"], value["x"])):
        role = str(point["role"])
        ingredient_id = palette.get(role)
        item, _ = catalog.resolve(ingredient_id or "")
        if not item:
            continue
        x = float(point["x"])
        y = float(point["y"])
        if organic:
            x += (rng.random() - 0.5) * 0.025
            y += (rng.random() - 0.5) * 0.025
        size = "Small" if role in {"dark", "white", "orange"} else "Medium"
        placements.append(
            ArtworkPlacement(
                ingredient_id=item.id,
                size=size,
                x=round(max(-0.92, min(0.92, x)), 4),
                y=round(max(-0.92, min(0.92, y)), 4),
                rotation=round(_placement_rotation(item, x, y, rng), 2),
                layer=int(point["layer"]),
                role=role,
            )
        )

    counts: Counter[tuple[str, str]] = Counter((item.ingredient_id, item.size) for item in placements)
    ingredients: list[RecipeIngredient] = []
    for (ingredient_id, size_name), count in sorted(counts.items(), key=lambda item: (-item[1], item[0][0])):
        catalog_item, _ = catalog.resolve(ingredient_id)
        if not catalog_item:
            continue
        size = catalog_item.size(size_name)
        ingredients.append(
            RecipeIngredient(
                id=catalog_item.id,
                size=size.size,
                target_grams=round(size.grams * count, 2),
                distribution="artistic",
                note="Precision artwork role: " + next(
                    (point.role for point in placements if point.ingredient_id == ingredient_id),
                    "color",
                ),
            )
        )

    subject = recipe.artwork.subject or template.replace("-", " ").title()
    recipe.name = (subject + " Pizza Art")[:60]
    recipe.summary = "A %s-detail %s rendered with %d deliberate ingredient placements." % (
        detail,
        subject,
        len(placements),
    )
    recipe.rationale = (
        "Color-role mapping, ingredient geometry, edge clipping, semantic layers and deterministic "
        "mosaic sampling preserve the recognizable artwork while the native game renders every piece."
    )
    recipe.ingredients = ingredients[:12]
    allowed = {item.id.casefold() for item in recipe.ingredients}
    recipe.placements = [item for item in placements if item.ingredient_id.casefold() in allowed]
    recipe.artwork = ArtworkMetadata(
        enabled=True,
        template=template,
        subject=subject,
        detail=detail,
        style="organic mosaic" if organic else "precision mosaic",
        piece_count=len(recipe.placements),
        symmetry=symmetry,
        algorithm="role raster + visual palette + symmetry studio + deterministic feature-priority sampling v1.1",
        source=source,
        palette={role: ingredient for role, ingredient in palette.items() if ingredient.casefold() in allowed},
        pixel_map=[],
    )
    recipe.warnings.append(
        "Artwork mode prioritizes recognizable color and placement; review native taste, cost and popularity before saving."
    )
    return recipe
