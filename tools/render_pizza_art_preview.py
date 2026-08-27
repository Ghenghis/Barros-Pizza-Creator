from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from barros_ai.models import Recipe  # noqa: E402
from barros_ai.pizza_art import compile_recipe_artwork, ingredient_visual_profile  # noqa: E402
from barros_ai.solver import CatalogIndex, repair_recipe  # noqa: E402


def render(template: str, detail: str, seed: int, vegan: bool, organic: bool, output: Path) -> None:
    payload = json.loads((ROOT / "backend" / "catalog.bootstrap.json").read_text(encoding="utf-8"))
    catalog = CatalogIndex.from_payload(payload["ingredients"])
    prompt = "%s-detail %s pizza art%s%s" % (
        detail,
        template,
        " vegan palette" if vegan else "",
        " organic handmade style" if organic else " precision style",
    )
    recipe = repair_recipe(
        compile_recipe_artwork(Recipe.from_dict({"name": "Preview"}), prompt, catalog, seed),
        catalog,
    )
    by_id = {item.id: item for item in catalog.ingredients}
    size = 720
    center = 360
    radius = 294
    circles: list[str] = []
    for placement in sorted(recipe.placements, key=lambda item: (item.layer, item.y, item.x)):
        ingredient = by_id[placement.ingredient_id]
        visual = ingredient_visual_profile(ingredient)
        x = center + placement.x * radius
        y = center - placement.y * radius
        piece_radius = 7.5 if placement.size == "Small" else 11.5
        circles.append(
            '<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s" stroke="#3A1F1A" stroke-opacity=".35" stroke-width="1" />'
            % (x, y, piece_radius, visual["hex"])
        )
    counts = Counter(item.ingredient_id for item in recipe.placements)
    legend = " · ".join("%s %d" % item for item in counts.most_common())
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="720" height="800" viewBox="0 0 720 800">
<rect width="720" height="800" rx="26" fill="#2A1716"/>
<circle cx="360" cy="360" r="322" fill="#D79D55" stroke="#8C482E" stroke-width="12"/>
<circle cx="360" cy="360" r="294" fill="#E8BF72" stroke="#F5DCA2" stroke-width="5"/>
%s
<text x="360" y="714" text-anchor="middle" fill="#FFF4E8" font-family="Arial" font-size="26" font-weight="700">%s · %s detail · %d pieces</text>
<text x="360" y="750" text-anchor="middle" fill="#EECFC2" font-family="Arial" font-size="15">%s</text>
<text x="360" y="776" text-anchor="middle" fill="#BFA79E" font-family="Arial" font-size="13">Algorithm preview — the game uses the same normalized placement plan with native 3D ingredients.</text>
</svg>
""" % (
        "\n".join(circles),
        html.escape(recipe.artwork.subject),
        html.escape(recipe.artwork.detail.title()),
        len(recipe.placements),
        html.escape(legend),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")
    print("Rendered %s with %d placements to %s" % (recipe.artwork.subject, len(recipe.placements), output))


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a dependency-free SVG proof of a Barro's pizza-art placement plan.")
    parser.add_argument("template", choices=("santa", "face", "heart", "tree", "smiley", "snowman", "star"))
    parser.add_argument("--detail", choices=("draft", "standard", "high"), default="high")
    parser.add_argument("--seed", type=int, default=1301)
    parser.add_argument("--vegan", action="store_true")
    parser.add_argument("--organic", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render(args.template, args.detail, args.seed, args.vegan, args.organic, args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
