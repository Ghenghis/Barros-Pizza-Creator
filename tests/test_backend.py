from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from barros_ai.models import Recipe  # noqa: E402
from barros_ai.orchestrator import PizzaOrchestrator, _enforce_request_constraints  # noqa: E402
from barros_ai.providers import ProviderClient, ProviderSettings  # noqa: E402
from barros_ai.providers import extract_json  # noqa: E402
from barros_ai.history import HistoryStore  # noqa: E402
from barros_ai.server import App, Handler, ThreadingHTTPServer  # noqa: E402
from barros_ai.solver import CatalogIndex, repair_recipe  # noqa: E402


CATALOG = [
    {"id": "Mozzarella", "type_id": "Cheese", "sizes": [{"size": "Large", "grams": 125, "cost": 1.2}, {"size": "Medium", "grams": 40, "cost": .38}, {"size": "Small", "grams": 2, "cost": .02}]},
    {"id": "Chicken", "type_id": "Meat", "sizes": [{"size": "Large", "grams": 150, "cost": 2}, {"size": "Medium", "grams": 30, "cost": .4}, {"size": "Small", "grams": 5, "cost": .07}]},
    {"id": "Jalapeno", "type_id": "Spice", "craziness": .4, "sizes": [{"size": "Large", "grams": 80, "cost": .5}, {"size": "Medium", "grams": 15, "cost": .1}, {"size": "Small", "grams": 2, "cost": .02}]},
    {"id": "Tomato", "type_id": "Vegetable", "sizes": [{"size": "Large", "grams": 100, "cost": .5}, {"size": "Medium", "grams": 20, "cost": .1}, {"size": "Small", "grams": 2, "cost": .01}]},
    {"id": "Onion", "type_id": "Vegetable", "sizes": [{"size": "Large", "grams": 140, "cost": .5}, {"size": "Medium", "grams": 20, "cost": .08}, {"size": "Small", "grams": 2, "cost": .01}]},
    {"id": "Pepper", "type_id": "Vegetable", "sizes": [{"size": "Large", "grams": 220, "cost": 1.7}, {"size": "Medium", "grams": 35, "cost": .27}, {"size": "Small", "grams": 4, "cost": .03}]},
    {"id": "Bacon", "type_id": "Meat", "sizes": [{"size": "Large", "grams": 100, "cost": 1.5}, {"size": "Medium", "grams": 20, "cost": .3}, {"size": "Small", "grams": 3, "cost": .04}]},
    {"id": "Chili", "type_id": "Spice", "sizes": [{"size": "Large", "grams": 50, "cost": .5}, {"size": "Medium", "grams": 10, "cost": .1}, {"size": "Small", "grams": 1, "cost": .01}]},
]


class BackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.orchestrator = PizzaOrchestrator(ProviderClient(ProviderSettings()))

    def test_invalid_ids_are_repaired_or_removed(self) -> None:
        recipe = Recipe.from_dict({"name": "x", "ingredients": [{"id": "Jalapeño"}, {"id": "Ranch"}, {"id": "Cooked Chicken"}]})
        result = repair_recipe(recipe, CatalogIndex.from_payload(CATALOG))
        self.assertEqual([x.id for x in result.ingredients], ["Jalapeno", "Chicken"])

    def test_offline_compose_is_deterministic_and_valid(self) -> None:
        payload = {"prompt": "Arizona hot chicken with jalapeños, profitable", "catalog": CATALOG, "constraints": {"heat": "hot"}}
        first = self.orchestrator.compose(payload)
        second = self.orchestrator.compose(payload)
        self.assertEqual(first["recipes"], second["recipes"])
        ids = {item["id"] for item in first["recipes"][0]["ingredients"]}
        self.assertIn("Chicken", ids)
        self.assertIn("Jalapeno", ids)
        self.assertNotIn("Ranch", ids)

    def test_lab_returns_three(self) -> None:
        result = self.orchestrator.compose({"prompt": "surprise", "catalog": CATALOG, "count": 3})
        self.assertEqual(len(result["recipes"]), 3)

    def test_checked_in_catalog_has_exact_game_inventory(self) -> None:
        catalog = json.loads((ROOT / "backend" / "catalog.bootstrap.json").read_text())
        self.assertEqual(len(catalog["ingredients"]), 87)
        self.assertEqual(
            {item["type_id"] for item in catalog["ingredients"]},
            {"Cheese", "Fish", "Fruit", "Meat", "Spice", "Vegetable"},
        )
        for item in catalog["ingredients"]:
            self.assertEqual([size["size"] for size in item["sizes"]], ["Large", "Medium", "Small"])

    def test_all_outputs_resolve_against_full_catalog(self) -> None:
        catalog = json.loads((ROOT / "backend" / "catalog.bootstrap.json").read_text())["ingredients"]
        valid = {item["id"] for item in catalog}
        prompts = [
            "spicy Arizona chicken",
            "Mediterranean vegetarian",
            "vegan green pizza",
            "Hawaiian with jalapeno",
            "mushroom gourmet",
            "surprise me",
        ]
        for prompt in prompts:
            response = self.orchestrator.compose({"prompt": prompt, "catalog": catalog, "count": 3})
            for recipe in response["recipes"]:
                self.assertGreaterEqual(len(recipe["ingredients"]), 2)
                self.assertLessEqual(len(recipe["ingredients"]), 8)
                self.assertTrue({item["id"] for item in recipe["ingredients"]}.issubset(valid))

    def test_explicit_exclusions_are_hard_constraints(self) -> None:
        result = self.orchestrator.compose(
            {
                "prompt": "Arizona chicken bacon pizza",
                "catalog": CATALOG,
                "constraints": {"exclude": ["Chicken", "Bacon", "Meat"]},
            }
        )
        ids = {item["id"] for item in result["recipes"][0]["ingredients"]}
        self.assertNotIn("Chicken", ids)
        self.assertNotIn("Bacon", ids)

    def test_prompt_dietary_exclusions_survive_provider_drafts(self) -> None:
        recipe = Recipe.from_dict(
            {
                "name": "Provider draft",
                "ingredients": [
                    {"id": "Chicken", "target_grams": 60},
                    {"id": "Bacon", "target_grams": 30},
                    {"id": "Tomato", "target_grams": 50},
                    {"id": "Onion", "target_grams": 40},
                ],
            }
        )
        result = _enforce_request_constraints(
            recipe, {}, CatalogIndex.from_payload(CATALOG), "Make this vegetarian"
        )
        ids = {item.id for item in result.ingredients}
        self.assertNotIn("Chicken", ids)
        self.assertNotIn("Bacon", ids)

    def test_price_ceiling_reduces_estimated_price(self) -> None:
        ceiling = 4.0
        result = self.orchestrator.compose(
            {
                "prompt": "hot chicken bacon pepper",
                "catalog": CATALOG,
                "constraints": {"price_ceiling": ceiling, "profit_factor": 0.6},
            }
        )
        recipe = result["recipes"][0]
        self.assertLessEqual(recipe["scores"]["cost"] * (1 + recipe["profit_factor"]), ceiling + 0.05)

    def test_improve_uses_current_pizza_context(self) -> None:
        result = self.orchestrator.compose(
            {
                "prompt": "Improve this while keeping its identity",
                "current_pizza": "Current ingredients: Chicken x4, Jalapeno x8",
                "catalog": CATALOG,
            }
        )
        ids = {item["id"] for item in result["recipes"][0]["ingredients"]}
        self.assertIn("Chicken", ids)
        self.assertIn("Jalapeno", ids)

    def test_offline_accepts_attachment_metadata(self) -> None:
        result = self.orchestrator.compose(
            {
                "prompt": "use the attached inspiration",
                "catalog": CATALOG,
                "attachments": [{"name": "reference.png", "mime_type": "image/png", "data_base64": "AA=="}],
            }
        )
        self.assertTrue(result["ok"])

    def test_json_extraction_handles_fenced_response(self) -> None:
        self.assertEqual(extract_json("```json\n{\"recipes\": []}\n```"), {"recipes": []})

    def test_history_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            history = HistoryStore(Path(folder) / "history.json", max_entries=2)
            for index in range(3):
                history.append("chat", str(index), {"ok": True})
            self.assertEqual([entry["prompt"] for entry in history.read()], ["1", "2"])

    def test_crew_has_all_personas(self) -> None:
        result = self.orchestrator.crew({"prompt": "a crowd favorite", "catalog": CATALOG})
        self.assertEqual([a["agent"] for a in result["agents"]], ["Flavor Chef", "Cost Manager", "Customer Scout", "Creative Director"])
        self.assertGreater(result["consensus"]["score"], 0)

    def test_http_health_and_compose(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            settings = root / "settings.json"
            settings.write_text('{"provider":"offline"}', encoding="utf-8")
            app = App(root, settings)
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            server.app = app
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                port = server.server_address[1]
                health = json.load(urllib.request.urlopen("http://127.0.0.1:%d/health" % port))
                self.assertTrue(health["ok"])
                request = urllib.request.Request(
                    "http://127.0.0.1:%d/compose" % port,
                    data=json.dumps({"prompt": "hot chicken", "catalog": CATALOG}).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                response = json.load(urllib.request.urlopen(request))
                self.assertTrue(response["ok"])
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
