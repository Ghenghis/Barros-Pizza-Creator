import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "rc1.acceptance.json"


class ProofContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_gate_ids_are_unique_and_release_requirements_have_evidence(self):
        gates = [gate for layer in self.contract["layers"] for gate in layer["gates"]]
        ids = [gate["id"] for gate in gates]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(gates), 20)
        for gate in gates:
            self.assertRegex(gate["id"], r"^[A-Z]{2,3}-\d{3}$")
            if gate["release_required"]:
                self.assertTrue(gate["evidence"].strip())

    def test_locked_reference_images_exist_and_match(self):
        self.assertEqual(4, len(self.contract["reference_images"]))
        for reference in self.contract["reference_images"]:
            path = ROOT / reference["path"]
            self.assertTrue(path.is_file(), path)
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(reference["sha256"], actual, reference["mode"])

    def test_certified_artifact_matches_provenance(self):
        provenance = json.loads((ROOT / "artifacts" / "build-provenance.json").read_text(encoding="utf-8"))
        artifact = ROOT / "artifacts" / provenance["artifact"]
        self.assertTrue(artifact.is_file())
        self.assertEqual(provenance["artifact_bytes"], artifact.stat().st_size)
        self.assertEqual(provenance["artifact_sha256"], hashlib.sha256(artifact.read_bytes()).hexdigest())
        self.assertEqual(
            self.contract["target"]["assembly_csharp_sha256"],
            provenance["target"]["assembly_csharp_sha256"],
        )
        source_lines = []
        for path in sorted((ROOT / "plugin-src").glob("*.cs"), key=lambda item: item.name):
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(provenance["source_files_sha256"][path.name], actual)
            source_lines.append(f"{actual}  plugin-src/{path.name}\n")
        source_tree = hashlib.sha256("".join(source_lines).encode("utf-8")).hexdigest()
        self.assertEqual(provenance["source_tree_sha256"], source_tree)

    def test_contract_names_all_requested_runtime_proofs(self):
        requirements = " ".join(
            gate["requirement"] for layer in self.contract["layers"] for gate in layer["gates"]
        ).lower()
        for term in ("fifth tab", "header", "preview", "restore", "apply", "save", "reload", "microphone", "speech provider", "chat", "lab", "crew", "voice"):
            self.assertIn(term, requirements)

    def test_bepinex_plugin_version_is_numeric_and_installer_is_target_scoped(self):
        plugin = (ROOT / "plugin-src" / "BarrosAiPlugin.cs").read_text(encoding="utf-8")
        match = re.search(r'BepInPlugin\([^\n]+,\s*"([^"]+)"\)\]', plugin)
        self.assertIsNotNone(match)
        self.assertRegex(match.group(1), r"^\d+\.\d+\.\d+$")

        installer = (ROOT / "INSTALL_Barros_AI_Designer.ps1").read_text(encoding="utf-8")
        self.assertIn("$targetExePath", installer)
        self.assertIn("$_.ExecutablePath", installer)
        self.assertNotIn("Get-Process -Name $processName", installer)

    def test_recipe_placement_spreads_across_ingredient_families(self):
        bridge = (ROOT / "plugin-src" / "GameBridge.cs").read_text(encoding="utf-8")
        self.assertIn("global * 2.399963229728653", bridge)
        self.assertNotIn("index * 2.399963229728653", bridge)
        self.assertIn("new Vector3(-3f + localX", bridge)

    def test_designer_panel_stays_clear_of_native_tab_rail(self):
        renderer = (ROOT / "plugin-src" / "PanelRenderer.cs").read_text(encoding="utf-8")
        self.assertIn("FitBesideTabRail(screenRect)", renderer)
        self.assertIn("tabScreenRect.xMax + gap", renderer)
        self.assertIn('"ui.panel_fitted"', renderer)

    def test_educational_and_audio_pipeline_assets_are_real_and_present(self):
        for relative in (
            "docs/ENGINEERING_PLAYBOOK.md",
            "docs/PROJECT_STATUS.md",
            "docs/AUDIO_PIPELINE.md",
            "scripts/Convert-BarrosMusic.ps1",
            "CONVERT_BARROS_MUSIC.bat",
            "tools/build_release.py",
        ):
            path = ROOT / relative
            self.assertTrue(path.is_file(), path)
            self.assertGreater(path.stat().st_size, 100, path)

        converter = (ROOT / "scripts" / "Convert-BarrosMusic.ps1").read_text(encoding="utf-8")
        self.assertIn(r"S:\Unity_Games\PC3 - Pizza Creator\Barros_Music", converter)
        self.assertIn('"libvorbis"', converter)
        self.assertIn("conversion-manifest.json", converter)

        release_builder = (ROOT / "tools" / "build_release.py").read_text(encoding="utf-8")
        self.assertIn("ALLOWED_ARTIFACTS", release_builder)
        self.assertIn("artifacts/Barros.PizzaCreator.AI.dll", release_builder)
        self.assertIn('(\"backend\", \"data\", \"inspiration\")', release_builder)

        manifest_paths = {
            line.split("  ", 1)[1]
            for line in (ROOT / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
        }
        self.assertEqual(
            {
                "artifacts/Barros.PizzaCreator.AI.dll",
                "artifacts/README.md",
                "artifacts/build-provenance.json",
            },
            {path for path in manifest_paths if path.startswith("artifacts/")},
        )

        bundled_audio = []
        for extension in ("*.wav", "*.mp3", "*.flac", "*.m4a", "*.aac", "*.wma", "*.aiff", "*.aif", "*.opus", "*.oga", "*.ogg"):
            bundled_audio.extend(ROOT.rglob(extension))
        self.assertEqual([], bundled_audio, "RC1 must not ship placeholder or unlicensed music")


if __name__ == "__main__":
    unittest.main()
