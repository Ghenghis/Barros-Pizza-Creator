import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class NativeJpegContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(
            (ROOT / "contracts" / "pc3-creator-native-jpeg.contract.json").read_text(encoding="utf-8")
        )

    def test_exact_export_facts_are_pinned(self):
        export = self.contract["native_jpeg_export"]
        self.assertEqual(export["source_width"], 2560)
        self.assertEqual(export["source_height"], 1440)
        self.assertEqual(export["resize_scale"], 0.5)
        self.assertEqual(export["output_width"], 1280)
        self.assertEqual(export["output_height"], 720)
        self.assertEqual(export["jpeg_quality"], 90)
        self.assertEqual(export["maximum_concurrent_files_per_name"], 5)
        self.assertTrue(export["writes_encoder_bytes_directly"])
        self.assertFalse(export["custom_metadata_insertion"])
        self.assertFalse(export["custom_recipe_payload"])
        self.assertFalse(export["native_jpeg_to_editable_pizza_importer"])

    def test_private_source_evidence_is_commit_and_blob_pinned(self):
        source = self.contract["source_evidence"]
        self.assertEqual(source["commit"], "d8fdd733fa068e00048441375a69feb8fd5b5440")
        files = source["files"]
        self.assertEqual(len(files), 9)
        self.assertEqual(len({entry["path"] for entry in files}), len(files))
        for entry in files:
            self.assertRegex(entry["blob_sha"], r"^[0-9a-f]{40}$")

    def test_recipe_is_a_separate_json_contract(self):
        recipe = self.contract["editable_recipe"]
        self.assertTrue(recipe["independent_from_jpeg_export"])
        self.assertIn("DoughPositions", recipe["serialized_fields"])
        self.assertIn("IngredientID", recipe["placement_fields"])
        self.assertIn("Position", recipe["placement_fields"])
        self.assertIn("Rotation", recipe["placement_fields"])
        self.assertIn("UserData/Recipes", recipe["output_directory"])

    def test_runtime_bridge_reuses_native_export_and_verifies_persistence(self):
        bridge = (ROOT / "plugin-src" / "GameBridge.cs").read_text(encoding="utf-8")
        plugin = (ROOT / "plugin-src" / "BarrosAiPlugin.cs").read_text(encoding="utf-8")
        panel = (ROOT / "plugin-src" / "PanelRenderer.cs").read_text(encoding="utf-8")
        self.assertIn("FindObjectsOfTypeAll<ScreenshotButton>()", bridge)
        self.assertIn("stockButton.specialScreenshotUI.SetActive(true)", bridge)
        self.assertIn("stockButton.screenCapture.Capture(fileName)", bridge)
        self.assertIn("File.Exists(savedRecipePath)", bridge)
        self.assertIn("serializer.DeserializeToObject<PizzaModel>(json)", bridge)
        self.assertIn("database.GetIngredientByID(placed.IngredientID, placed.Size)", bridge)
        self.assertIn("public bool ReloadLastSaved(out string detail)", bridge)
        self.assertIn("game.ReloadLastSaved(out detail)", plugin)
        self.assertIn('"Export stock JPG"', panel)

    def test_public_release_does_not_vendor_private_decompiled_source(self):
        self.assertFalse((ROOT / "pizza-creator" / "Assembly-CSharp").exists())
        self.assertFalse((ROOT / "pc3-base" / "Assembly-CSharp").exists())


if __name__ == "__main__":
    unittest.main()
