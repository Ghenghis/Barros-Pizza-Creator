import importlib.util
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


class SharedControlledStimulusDiffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.diff = load_script("compare_controlled_stimuli.py")

    @staticmethod
    def fixture(case_id="a", yaw=0.0, x=-3.0):
        return {
            "schema_version": "1.0",
            "experiment_id": "E01",
            "case_id": case_id,
            "runtime_profile": "creator-0.11.272",
            "model": {
                "name": "JPEG-E01-CONTROLLED",
                "shape": "Round",
                "profit_factor": 1.0,
                "placements": [
                    {
                        "ingredient_id": "Bacon",
                        "size": "Medium",
                        "position": {"x": x, "y": 1.0, "z": 0.0},
                        "rotation": {"x": 0.0, "y": yaw, "z": 0.0},
                    }
                ],
            },
            "operation": {
                "preview_exact_model": True,
                "native_recipe_save": True,
                "reload_verify": False,
                "native_resave_after_reload": False,
            },
            "notes": "controlled evidence label",
        }

    def test_rotation_pair_passes_rotation_only_allow_rule(self):
        a = self.fixture("yaw-000", 0.0)
        b = self.fixture("yaw-090", 90.0)
        result = self.diff.compare(a, b, ["model.placements[*].rotation.y"])
        self.assertTrue(result["allowed_check_pass"])
        self.assertEqual(result["unexpected_substantive_changes"], [])
        self.assertEqual(result["substantive_changed_field_families"], ["model.placements[*].rotation.y"])
        self.assertIn("case_id", result["evidence_label_changed_fields"])

    def test_rotation_rule_rejects_hidden_x_change(self):
        a = self.fixture("yaw-000", 0.0)
        b = self.fixture("yaw-090", 90.0, x=-2.5)
        result = self.diff.compare(a, b, ["model.placements[*].rotation.y"])
        self.assertFalse(result["allowed_check_pass"])
        self.assertIn("model.placements[0].position.x", result["unexpected_substantive_changes"])

    def test_shared_schema_allows_empty_e00_placement_array(self):
        fixture = self.fixture("repeat-01", 0.0)
        fixture["experiment_id"] = "E00"
        fixture["model"]["name"] = "JPEG-E00-IDENTICAL"
        fixture["model"]["placements"] = []
        self.diff.validate_fixture(fixture)


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
