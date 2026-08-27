import hashlib
import json
import sys
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

    def test_artifact_provenance_is_truthful_for_current_source(self):
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
        actual_sources = {}
        for path in sorted((ROOT / "plugin-src").glob("*.cs"), key=lambda item: item.name):
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            actual_sources[path.name] = actual
            source_lines.append(f"{actual}  plugin-src/{path.name}\n")
        source_tree = hashlib.sha256("".join(source_lines).encode("utf-8")).hexdigest()
        source_current = provenance["source_files_sha256"] == actual_sources

        sys.path.insert(0, str(ROOT / "tools"))
        try:
            from artifact_provenance import inspect

            status = inspect(ROOT)
        finally:
            sys.path.pop(0)
        self.assertEqual(source_current, status["source_hashes_match"])
        self.assertEqual(source_tree == provenance["source_tree_sha256"], status["source_tree_hash_matches"])
        if source_current:
            self.assertTrue(status["certified_prebuilt_current"])
        else:
            self.assertFalse(status["certified_prebuilt_current"])
            self.assertGreater(len(status["mismatched_source_files"]), 0)
            self.assertIn("exact Windows rebuild required", status["reason"])

    def test_package_omits_a_stale_prebuilt_and_installer_checks_sources(self):
        sys.path.insert(0, str(ROOT / "tools"))
        try:
            from artifact_provenance import inspect
            from build_release import build, package_files

            status = inspect(ROOT)
            packaged = {
                path.relative_to(ROOT).as_posix()
                for path in package_files(ROOT, status["certified_prebuilt_current"])
            }
        finally:
            sys.path.pop(0)

        certified = {
            "artifacts/Barros.PizzaCreator.AI.dll",
            "artifacts/build-provenance.json",
        }
        if status["certified_prebuilt_current"]:
            self.assertTrue(certified.issubset(packaged))
        else:
            self.assertTrue(certified.isdisjoint(packaged))
            with self.assertRaisesRegex(RuntimeError, "Release promotion blocked"):
                build(ROOT / "releases" / ".must-not-be-written.zip", require_certified_artifact=True)
        installer = (ROOT / "INSTALL_Barros_AI_Designer.ps1").read_text(encoding="utf-8")
        self.assertIn("function Test-SourceProvenance", installer)
        self.assertIn("Test-SourceProvenance $provenance", installer)

    def test_contract_names_all_requested_runtime_proofs(self):
        requirements = " ".join(
            gate["requirement"] for layer in self.contract["layers"] for gate in layer["gates"]
        ).lower()
        for term in ("fifth tab", "header", "preview", "restore", "apply", "save", "reload", "microphone", "speech provider", "chat", "lab", "crew", "voice"):
            self.assertIn(term, requirements)

    def test_educational_and_audio_pipeline_assets_are_real_and_present(self):
        for relative in (
            "docs/ENGINEERING_PLAYBOOK.md",
            "docs/PROJECT_STATUS.md",
            "docs/AUDIO_PIPELINE.md",
            "scripts/Convert-BarrosMusic.ps1",
            "CONVERT_BARROS_MUSIC.bat",
            "tools/build_release.py",
            "tools/artifact_provenance.py",
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

        self.assertIn("CERTIFIED_ARTIFACTS", release_builder)
        self.assertIn("source-local-compile-required", release_builder)

        bundled_audio = []
        for extension in ("*.wav", "*.mp3", "*.flac", "*.m4a", "*.aac", "*.wma", "*.aiff", "*.aif", "*.opus", "*.oga", "*.ogg"):
            bundled_audio.extend(ROOT.rglob(extension))
        self.assertEqual([], bundled_audio, "RC1 must not ship placeholder or unlicensed music")


if __name__ == "__main__":
    unittest.main()
