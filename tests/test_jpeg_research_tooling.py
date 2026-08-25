import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".", "_"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class JpegEncoderFingerprintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fp = load_script("fingerprint_jpeg_encoder.py")

    def test_ijg_quality_75_luma_has_known_scaled_coefficients(self):
        values = self.fp.scale_ijg_table(self.fp.LUMA_NATURAL, 75)
        self.assertEqual(len(values), 64)
        # Standard q=75 luma natural table starts 8,6,5,8...; JPEG DQT is zigzag.
        self.assertEqual(values[:8], [8, 6, 6, 7, 6, 5, 8, 7])
        self.assertEqual(self.fp.exact_quality_matches(values, self.fp.LUMA_NATURAL), [75])

    def test_joint_quality_match_requires_both_tables(self):
        luma = self.fp.scale_ijg_table(self.fp.LUMA_NATURAL, 90)
        chroma = self.fp.scale_ijg_table(self.fp.CHROMA_NATURAL, 90)
        parsed = {
            "frame": {"kind": "SOF0_baseline_dct"},
            "quantization_tables": {
                "0": {"precision_bits": 8, "values_zigzag_order": luma, "sha256": "l"},
                "1": {"precision_bits": 8, "values_zigzag_order": chroma, "sha256": "c"},
            },
            "huffman_tables": [],
            "restart_interval": None,
            "app_markers": [],
            "comments": [],
            "scan_count": 1,
            "is_progressive": False,
        }
        result = self.fp.fingerprint(parsed)
        self.assertEqual(result["ijg_standard_quality_match"]["joint_exact_candidates"], [90])
        self.assertTrue(result["ijg_standard_quality_match"]["exact_joint_match"])


class FixtureGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fx = load_script("generate_jpeg_experiment_fixtures.py")

    @staticmethod
    def base_fixture():
        return {
            "schema_version": "1.0",
            "experiment_id": "BASE",
            "variant": "BASE",
            "runtime_profile": "creator-0.11.272",
            "name": "BASE",
            "shape": "Round",
            "profit_factor": 0.6,
            "placements": [
                {
                    "sequence": 0,
                    "ingredient_id": "Bacon",
                    "size": "Medium",
                    "position": {"x": -3.0, "y": 1.0, "z": 0.0},
                    "rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
                },
                {
                    "sequence": 1,
                    "ingredient_id": "Chicken",
                    "size": "Small",
                    "position": {"x": -2.5, "y": 1.01, "z": 0.5},
                    "rotation": {"x": 0.0, "y": 15.0, "z": 0.0},
                },
            ],
        }

    def test_rotation_variant_diff_proof_allows_only_rotation_family(self):
        base = self.base_fixture()
        label, variant, allowed = next(item for item in self.fx.rotation_variants(base) if item[0] == "R090")
        proof = self.fx.diff_proof(base, variant, allowed, "E01", label)
        self.assertTrue(proof["valid_one_variable_family"])
        self.assertEqual(proof["unexpected_changes"], [])
        self.assertIn("placements[*].rotation.y", proof["observed_changed_field_families"])
        self.assertNotIn("placements[*].position.x", proof["observed_changed_field_families"])

    def test_unexpected_position_change_is_rejected_by_rotation_rule(self):
        base = self.base_fixture()
        label, variant, allowed = next(item for item in self.fx.rotation_variants(base) if item[0] == "R090")
        variant["placements"][0]["position"]["x"] = -2.75
        proof = self.fx.diff_proof(base, variant, allowed, "E01", label)
        self.assertFalse(proof["valid_one_variable_family"])
        self.assertIn("placements[0].position.x", proof["unexpected_changes"])

    def test_e09_reverse_order_preserves_same_placement_records_as_a_multiset(self):
        base = self.base_fixture()
        variants = {label: fixture for label, fixture, _ in self.fx.e09_variants(base, 90.0, 0.35, 0.2)}
        a = variants["A"]
        d = variants["D"]

        def identity_without_sequence(item):
            item = json.loads(json.dumps(item))
            item.pop("sequence", None)
            return json.dumps(item, sort_keys=True)

        self.assertEqual(
            sorted(identity_without_sequence(x) for x in a["placements"]),
            sorted(identity_without_sequence(x) for x in d["placements"]),
        )
        self.assertNotEqual(
            [x["ingredient_id"] for x in a["placements"]],
            [x["ingredient_id"] for x in d["placements"]],
        )


class StaticSourceTracerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tracer = load_script("trace_native_jpeg_source.py")

    def test_multistage_method_ranks_above_single_clue_method(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "SaveImage.cs").write_text(
                """
namespace Test {
class SaveImage {
public void SavePizza() {
    SaveCurrentPizzaToRecipes();
    RenderTexture rt = new RenderTexture(10,10,0);
    texture.ReadPixels(rect,0,0);
    byte[] jpeg = ImageConversion.EncodeToJPG(texture, 75);
    File.WriteAllBytes(\"pizza.jpg\", jpeg);
}
public void MentionTexture() {
    Texture2D t = null;
}
}
}
""",
                encoding="utf-8",
            )
            hits, mapping = self.tracer.scan_file(root, root / "SaveImage.cs")
            candidates = self.tracer.merge_candidates([mapping])

        self.assertGreater(len(hits), 0)
        by_method = {item["method"]: item for item in candidates}
        self.assertIn("SavePizza", by_method)
        self.assertIn("MentionTexture", by_method)
        self.assertGreater(by_method["SavePizza"]["score"], by_method["MentionTexture"]["score"])
        self.assertIn("jpeg_encoder", by_method["SavePizza"]["categories"])
        self.assertIn("file_write", by_method["SavePizza"]["categories"])


if __name__ == "__main__":
    unittest.main()
