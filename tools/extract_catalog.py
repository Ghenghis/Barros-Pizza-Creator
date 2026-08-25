from __future__ import annotations

import argparse
import json
from pathlib import Path


SIZES = ("Large", "Medium", "Small")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Pizza Creator ingredient JSON into the AI catalog schema.")
    parser.add_argument("game_dir", help="Folder containing 'Pizza Connection 3 - Pizza Creator_Data'.")
    parser.add_argument("--output", default="catalog.json")
    args = parser.parse_args()
    base = Path(args.game_dir).resolve()
    ingredients_dir = base / "Pizza Connection 3 - Pizza Creator_Data" / "StreamingAssets" / "Ingredients"
    if not ingredients_dir.is_dir():
        raise SystemExit("Ingredient folder not found: %s" % ingredients_dir)
    records = []
    for path in sorted(ingredients_dir.glob("*.json")):
        for item in json.loads(path.read_text(encoding="utf-8-sig")):
            amounts = item.get("Amounts") or []
            sizes = []
            for index, size in enumerate(SIZES):
                grams = float(amounts[index]) if index < len(amounts) else 0.0
                sizes.append(
                    {
                        "size": size,
                        "grams": grams,
                        "cost": round((grams / 100.0) * float(item.get("BasePrice", 0)), 4),
                    }
                )
            records.append(
                {
                    "id": item["ID"],
                    "name": item["ID"],
                    "type_id": item.get("TypeID", path.stem),
                    "base_price_per_100g": float(item.get("BasePrice", 0)),
                    "craziness": float(item.get("Craziness", 0)),
                    "sizes": sizes,
                }
            )
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"version": 1, "ingredients": records}, indent=2), encoding="utf-8")
    print("Wrote %d ingredients to %s" % (len(records), output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

