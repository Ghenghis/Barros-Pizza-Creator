from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from barros_ai.ingredient_intelligence import (  # noqa: E402
    ingredient_profile,
    ingredient_set_cohesion,
    suggest_pairings,
)
from barros_ai.inspiration import InspirationLibrary  # noqa: E402
from barros_ai.models import CatalogIngredient  # noqa: E402
from barros_ai.orchestrator import PizzaOrchestrator  # noqa: E402
from barros_ai.providers import ProviderClient, ProviderSettings  # noqa: E402
from barros_ai.solver import CatalogIndex  # noqa: E402


def fake_jpeg(width: int, height: int) -> bytes:
    sof_payload = b"\x08" + height.to_bytes(2, "big") + width.to_bytes(2, "big") + b"\x01\x01\x11\x00"
    sof = b"\xff\xc0" + (len(sof_payload) + 2).to_bytes(2, "big") + sof_payload
    return b"\xff\xd8" + sof + b"\xff\xd9"


class IngredientIntelligenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        payload = json.loads((ROOT / "backend" / "catalog.bootstrap.json").read_text(encoding="utf-8"))
        cls.catalog = CatalogIndex.from_payload(payload["ingredients"])

    def test_every_exact_game_ingredient_has_a_compact_profile(self) -> None:
        self.assertEqual(87, len(self.catalog.ingredients))
        for item in self.catalog.ingredients:
            profile = ingredient_profile(item)
            self.assertTrue(profile["display_name"])
            self.assertGreaterEqual(len(profile["flavor"]), 1)
            self.assertIsInstance(profile["dietary"], list)
            self.assertIsInstance(profile["allergens"], list)

    def test_named_anchor_attracts_curated_pairings(self) -> None:
        suggestions = suggest_pairings(["Chicken"], self.catalog.ingredients, limit=6)
        self.assertIn("Garlic", suggestions)
        self.assertIn("Jalapeno", suggestions)

    def test_known_pairings_score_above_unfocused_single_family_mix(self) -> None:
        coherent = [self.catalog.resolve(value)[0] for value in ("Mozzarella", "Tomato", "Basil")]
        unfocused = [self.catalog.resolve(value)[0] for value in ("Banana", "Kiwi", "Grapes")]
        self.assertGreater(
            ingredient_set_cohesion([item for item in coherent if item]),
            ingredient_set_cohesion([item for item in unfocused if item]),
        )


class InspirationLibraryTests(unittest.TestCase):
    def test_importer_deduplicates_and_library_selects_at_most_three(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source"
            library_root = root / "library"
            source.mkdir()
            (source / "spicy-chicken-pizza.jpg").write_bytes(fake_jpeg(800, 600))
            (source / "duplicate.jpg").write_bytes(fake_jpeg(800, 600))
            (source / "garden-pizza.jpg").write_bytes(fake_jpeg(640, 480))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "import_inspiration_images.py"),
                    str(source),
                    "--library-dir",
                    str(library_root),
                    "--rights",
                    "user-owned",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("1 duplicates", completed.stdout)
            library = InspirationLibrary(library_root)
            self.assertEqual(2, library.status()["count"])
            attachments, public = library.attachments_for_prompt("spicy chicken")
            self.assertEqual(2, len(attachments))
            self.assertEqual(2, len(public))
            self.assertLessEqual(len(attachments), 3)
            self.assertNotIn("data_base64", public[0])

    def test_offline_response_never_claims_visual_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            library_root = Path(folder)
            images = library_root / "images"
            images.mkdir()
            image_path = images / "idea.jpg"
            raw = fake_jpeg(320, 240)
            image_path.write_bytes(raw)
            (library_root / "index.json").write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "id": "idea",
                                "name": "idea.jpg",
                                "path": "images/idea.jpg",
                                "sha256": "placeholder",
                                "mime_type": "image/jpeg",
                                "format": "JPEG",
                                "bytes": len(raw),
                                "tags": ["pizza"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            catalog_payload = json.loads((ROOT / "backend" / "catalog.bootstrap.json").read_text(encoding="utf-8"))
            orchestrator = PizzaOrchestrator(
                ProviderClient(ProviderSettings(provider="offline")), InspirationLibrary(library_root)
            )
            response = orchestrator.compose(
                {
                    "prompt": "surprise pizza",
                    "catalog": catalog_payload["ingredients"],
                    "use_inspiration_library": True,
                }
            )
            self.assertFalse(response["inspiration_analyzed"])
            self.assertFalse(response["inspiration_sent_to_provider"])
            self.assertIn("needs an online vision provider", response["message"])

            class RecordingProvider:
                settings = ProviderSettings(provider="openai-compatible")
                online = True
                attachments: list[dict] = []

                def complete_multimodal(self, system, user, attachments, temperature=0.65, **_kwargs):
                    self.attachments = attachments
                    return json.dumps(
                        {
                            "recipes": [
                                {
                                    "name": "Provider Pizza",
                                    "shape": "Round",
                                    "ingredients": [
                                        {
                                            "id": "Mozzarella",
                                            "size": "Medium",
                                            "target_grams": 80,
                                            "distribution": "even",
                                        }
                                    ],
                                }
                            ]
                        }
                    )

            provider = RecordingProvider()
            online = PizzaOrchestrator(provider, InspirationLibrary(library_root))
            completed = online.compose(
                {
                    "prompt": "surprise pizza",
                    "catalog": catalog_payload["ingredients"],
                    "use_inspiration_library": True,
                }
            )
            self.assertTrue(provider.attachments)
            self.assertTrue(completed["inspiration_sent_to_provider"])
            self.assertIsNone(completed["inspiration_analyzed"])
            self.assertIn("sent 1 local inspiration image", completed["message"])


if __name__ == "__main__":
    unittest.main()
