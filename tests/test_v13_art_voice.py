from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from barros_ai.models import Recipe  # noqa: E402
from barros_ai.orchestrator import PizzaOrchestrator  # noqa: E402
from barros_ai.pizza_art import (  # noqa: E402
    TEMPLATES,
    compile_recipe_artwork,
    ingredient_visual_profile,
)
from barros_ai.providers import ProviderClient, ProviderSettings  # noqa: E402
from barros_ai.solver import CatalogIndex, repair_recipe  # noqa: E402
from barros_ai.tts import AGENT_VOICES, VOICE_LIBRARY, AzureSpeechService, safe_speech_text  # noqa: E402


class _FakeResponse:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return self.body


class PizzaArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        payload = json.loads((ROOT / "backend" / "catalog.bootstrap.json").read_text(encoding="utf-8"))
        cls.catalog_payload = payload["ingredients"]
        cls.catalog = CatalogIndex.from_payload(cls.catalog_payload)

    def compile(self, template: str, detail: str = "high", seed: int = 1301, extra: str = "") -> Recipe:
        recipe = Recipe.from_dict({"name": "Artwork", "ingredients": []})
        prompt = "%s-detail %s pizza art picture %s" % (detail, template, extra)
        return repair_recipe(compile_recipe_artwork(recipe, prompt, self.catalog, seed), self.catalog)

    def test_all_exact_game_ingredients_have_renderable_visual_metadata(self) -> None:
        self.assertEqual(87, len(self.catalog.ingredients))
        for item in self.catalog.ingredients:
            visual = ingredient_visual_profile(item)
            self.assertRegex(visual["hex"], r"^#[0-9A-F]{6}$")
            self.assertEqual(3, len(visual["rgb"]))
            self.assertTrue(visual["geometry"])
            self.assertGreater(visual["footprint"], 0)

    def test_all_templates_compile_to_bounded_exact_placements(self) -> None:
        for template in TEMPLATES:
            with self.subTest(template=template):
                recipe = self.compile(template)
                self.assertTrue(recipe.artwork.enabled)
                self.assertGreaterEqual(len(recipe.placements), 90)
                self.assertLessEqual(len(recipe.placements), 180)
                self.assertEqual(len(recipe.placements), recipe.artwork.piece_count)
                self.assertTrue(all(item.x * item.x + item.y * item.y <= 0.93**2 for item in recipe.placements))

    def test_detail_setting_changes_real_piece_count(self) -> None:
        draft = self.compile("santa", "draft")
        standard = self.compile("santa", "standard")
        high = self.compile("santa", "high")
        self.assertLess(len(draft.placements), len(standard.placements))
        self.assertLess(len(standard.placements), len(high.placements))
        self.assertEqual(176, len(high.placements))

    def test_santa_preserves_readable_feature_roles(self) -> None:
        roles = {item.role for item in self.compile("santa").placements}
        self.assertTrue({"red", "white", "skin", "dark"}.issubset(roles))

    def test_art_is_seed_deterministic_and_remixable(self) -> None:
        first = self.compile("face", seed=44)
        repeat = self.compile("face", seed=44)
        remix = self.compile("face", seed=45)
        self.assertEqual(first.to_dict(), repeat.to_dict())
        self.assertNotEqual(
            [(item.x, item.y, item.rotation) for item in first.placements],
            [(item.x, item.y, item.rotation) for item in remix.placements],
        )

    def test_vegan_palette_avoids_meat_fish_and_dairy(self) -> None:
        recipe = self.compile("santa", extra="vegan palette")
        by_id = {item.id: item for item in self.catalog.ingredients}
        for item in recipe.ingredients:
            if item.id in {"VeganCheese", "VeganSausage", "Tofu"}:
                continue
            self.assertNotIn(by_id[item.id].type_id, {"Cheese", "Fish", "Meat"})

    def test_provider_pixel_map_becomes_valid_native_placements(self) -> None:
        recipe = Recipe.from_dict(
            {
                "name": "Provider art",
                "artwork": {
                    "enabled": True,
                    "template": "custom",
                    "subject": "Tiny gift",
                    "detail": "standard",
                    "pixel_map": ["..RRR..", ".RWWW R.".replace(" ", ""), "RRK.KRR", ".RRRRR.", "..RRR.."],
                },
            }
        )
        compiled = repair_recipe(
            compile_recipe_artwork(recipe, "custom pizza art", self.catalog, 99), self.catalog
        )
        self.assertEqual("provider-pixel-map", compiled.artwork.source)
        self.assertEqual("custom", compiled.artwork.template)
        self.assertGreater(len(compiled.placements), 10)
        self.assertTrue({"red", "white", "dark"}.issubset({item.role for item in compiled.placements}))

    def test_offline_orchestrator_builds_high_detail_santa(self) -> None:
        orchestrator = PizzaOrchestrator(ProviderClient(ProviderSettings(provider="offline")))
        response = orchestrator.compose(
            {
                "prompt": "Create high-detail Santa Claus pizza artwork",
                "catalog": self.catalog_payload,
                "seed": 1301,
            }
        )
        recipe = response["recipes"][0]
        self.assertTrue(recipe["artwork"]["enabled"])
        self.assertEqual(176, len(recipe["placements"]))
        self.assertIn("176", response["message"])

    def test_builtin_template_skips_slow_online_provider(self) -> None:
        class MustNotRunProvider:
            settings = ProviderSettings(provider="openai-compatible")
            online = True
            calls = 0

            def complete_multimodal(self, *_args, **_kwargs):
                self.calls += 1
                raise AssertionError("Built-in art should not wait for the online provider")

        provider = MustNotRunProvider()
        orchestrator = PizzaOrchestrator(provider)
        response = orchestrator.compose(
            {
                "prompt": "Create a high-detail Santa pizza picture",
                "catalog": self.catalog_payload,
                "seed": 1301,
            }
        )
        self.assertEqual(0, provider.calls)
        self.assertFalse(response["provider_used"])
        self.assertEqual(176, len(response["recipes"][0]["placements"]))
        self.assertIn("compiled locally", response["message"])

    def test_focused_agent_interaction_returns_one_persona(self) -> None:
        orchestrator = PizzaOrchestrator(ProviderClient(ProviderSettings(provider="offline")))
        response = orchestrator.crew(
            {
                "prompt": "Review this pizza",
                "catalog": self.catalog_payload,
                "focus_agent": "Creative Director",
            }
        )
        self.assertEqual(["Creative Director"], [item["agent"] for item in response["agents"]])
        self.assertIn("focused review", response["message"])

    def test_online_agent_uses_short_timeout_and_local_fallback(self) -> None:
        class StalledProvider:
            settings = ProviderSettings(provider="openai-compatible")
            online = True
            request_options = None

            def complete(self, *_args, **kwargs):
                self.request_options = kwargs
                raise TimeoutError("simulated gateway stall")

        provider = StalledProvider()
        orchestrator = PizzaOrchestrator(provider)
        response = orchestrator.crew(
            {
                "prompt": "Review this pizza",
                "catalog": self.catalog_payload,
                "focus_agent": "Creative Director",
            }
        )
        opinion = response["agents"][0]
        self.assertEqual({"timeout_seconds": 25, "retries": 0}, provider.request_options)
        self.assertEqual("fallback", opinion["status"])
        self.assertIn("Local fallback:", opinion["message"])
        self.assertNotIn("Unavailable", opinion["message"])

    def test_plugin_source_contains_native_art_and_compact_controls(self) -> None:
        panel = (ROOT / "plugin-src" / "PanelRenderer.cs").read_text(encoding="utf-8")
        bridge = (ROOT / "plugin-src" / "GameBridge.cs").read_text(encoding="utf-8")
        self.assertIn("DrawArtStudio", panel)
        self.assertIn("for (int row = 0; row < 2; row++)", panel)
        self.assertIn("Agent voices", panel)
        self.assertIn('"Asking " + request.FocusAgent + " for a focused review…"', panel)
        self.assertIn("PositionForArtwork", bridge)
        self.assertIn("const int maximumPlacements = 180;", bridge)
        self.assertIn("globalIndex < maximumPlacements", bridge)

    def test_symmetry_studio_compiles_mirror_and_radial_layouts(self) -> None:
        mirrored = self.compile("santa", extra="mirror symmetry")
        radial = self.compile("star", extra="radial symmetry")
        self.assertEqual("mirror", mirrored.artwork.symmetry)
        self.assertEqual("radial", radial.artwork.symmetry)
        self.assertGreater(len(mirrored.placements), 80)
        self.assertGreater(len(radial.placements), 40)


class AgentVoiceTests(unittest.TestCase):
    def test_full_voice_library_has_24_balanced_english_voices(self) -> None:
        self.assertEqual(24, len(VOICE_LIBRARY))
        self.assertEqual(12, sum(item.gender == "female" for item in VOICE_LIBRARY))
        self.assertEqual(12, sum(item.gender == "male" for item in VOICE_LIBRARY))
        self.assertGreaterEqual(len({item.locale for item in VOICE_LIBRARY}), 9)

    def test_agent_voice_roster_uses_requested_uk_and_australian_locales(self) -> None:
        self.assertEqual({"en-GB", "en-AU"}, {item.locale for item in AGENT_VOICES.values()})
        self.assertEqual("en-GB-MaisieNeural", AGENT_VOICES["flavor chef"].voice)
        self.assertEqual("en-AU-CarlyNeural", AGENT_VOICES["creative director"].voice)

    def test_speech_filter_removes_urls_paths_and_code(self) -> None:
        filtered = safe_speech_text("Great crust. https://secret.test C:\\private\\key ```token-value```")
        self.assertEqual("Great crust.", filtered)

    def test_azure_request_uses_ssml_and_returns_wav(self) -> None:
        settings = ProviderSettings(
            tts_provider="azure",
            tts_region="australiaeast",
            tts_key="test-only-key",
        )
        service = AzureSpeechService(settings)
        observed = {}

        def fake_open(request, timeout):
            observed["request"] = request
            observed["timeout"] = timeout
            return _FakeResponse(b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 40)

        with patch("urllib.request.urlopen", fake_open):
            audio, profile, spoken = service.synthesize(
                "Cost Manager", "Keep the ingredient cost under control.", rate=1.1
            )
        request = observed["request"]
        self.assertTrue(service.configured)
        self.assertEqual(
            "https://australiaeast.tts.speech.microsoft.com/cognitiveservices/v1",
            request.full_url,
        )
        self.assertIn(b"en-AU-DarrenNeural", request.data)
        self.assertIn(b"<prosody rate='+10%'>", request.data)
        self.assertEqual("riff-24khz-16bit-mono-pcm", request.get_header("X-microsoft-outputformat"))
        self.assertEqual("Darren · Australia", profile.label)
        self.assertEqual("Keep the ingredient cost under control.", spoken)
        self.assertTrue(audio.startswith(b"RIFF"))


if __name__ == "__main__":
    unittest.main()
