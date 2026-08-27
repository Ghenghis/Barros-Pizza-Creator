from __future__ import annotations

import json
import re
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from barros_ai.server import App, Handler, ThreadingHTTPServer  # noqa: E402


class LiveContractHttpTests(unittest.TestCase):
    def _get(self, path: str, contract_payload: dict | None = None) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as folder:
            # Mirror both source and installed topology: App.root is backend while
            # the acceptance contract is its sibling under package/contracts.
            package = Path(folder) / "BarrosAI"
            backend = package / "backend"
            backend.mkdir(parents=True)
            settings = backend / "settings.json"
            settings.write_text('{"provider":"offline"}', encoding="utf-8")
            contract_dir = package / "contracts"
            contract_dir.mkdir(parents=True)
            payload = contract_payload
            if payload is None:
                payload = json.loads((ROOT / "contracts" / "rc1.acceptance.json").read_text(encoding="utf-8"))
            (contract_dir / "rc1.acceptance.json").write_text(
                json.dumps(payload, indent=2), encoding="utf-8"
            )
            app = App(backend, settings)
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            server.app = app
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                port = server.server_address[1]
                try:
                    response = urllib.request.urlopen(f"http://127.0.0.1:{port}{path}")
                    return response.status, json.load(response)
                except urllib.error.HTTPError as exc:
                    return exc.code, json.loads(exc.read().decode("utf-8"))
            finally:
                server.shutdown()
                server.server_close()

    def test_health_advertises_contract_surface(self) -> None:
        status, health = self._get("/health")
        self.assertEqual(200, status)
        self.assertTrue(health["capabilities"]["contract"])

    def test_contract_surface_works_from_installed_backend_sibling_layout(self) -> None:
        status_code, status = self._get("/contract")
        self.assertEqual(200, status_code)
        self.assertTrue(status["ok"])
        self.assertEqual("barros-pc3-rc1", status["contract_id"])
        self.assertEqual("0.11.272", status["target"]["game_version"])
        self.assertEqual(40, status["gate_count"])
        self.assertEqual(37, status["release_required_gate_count"])
        self.assertEqual(40, status["declared_states"]["not_run"])
        self.assertEqual("not_evaluated", status["certification"]["state"])
        self.assertFalse(status["certification"]["runtime_certified"])
        self.assertIn("retained evidence", status["certification"]["reason"])

    def test_contract_surface_rejects_non_array_layers(self) -> None:
        code, body = self._get("/contract", {"contract_id": "bad", "layers": {}})
        self.assertEqual(500, code)
        self.assertFalse(body["ok"])
        self.assertIn("layers must be a JSON array", body["error"])

    def test_contract_surface_rejects_non_object_gates(self) -> None:
        code, body = self._get(
            "/contract",
            {"contract_id": "bad", "layers": [{"id": "L0", "gates": ["not-an-object"]}]},
        )
        self.assertEqual(500, code)
        self.assertFalse(body["ok"])
        self.assertIn("gates must be a JSON array of objects", body["error"])

    def test_rc1_contract_release_matches_product_version(self) -> None:
        contract = json.loads((ROOT / "contracts" / "rc1.acceptance.json").read_text(encoding="utf-8"))
        version_text = (ROOT / "VERSION.txt").read_text(encoding="utf-8")
        match = re.search(r"^Version:\s*(\S+)\s*$", version_text, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), contract["release"])

    def test_installer_and_release_builder_use_product_version(self) -> None:
        version_text = (ROOT / "VERSION.txt").read_text(encoding="utf-8")
        match = re.search(r"^Version:\s*(\S+)\s*$", version_text, re.MULTILINE)
        self.assertIsNotNone(match)
        version = match.group(1)

        installer = (ROOT / "INSTALL_Barros_AI_Designer.ps1").read_text(encoding="utf-8")
        builder = (ROOT / "tools" / "build_release.py").read_text(encoding="utf-8")
        self.assertIn(f'$version = "{version}"', installer)
        self.assertIn(f"Barros_Pizza_Creator_AI_Designer_v{version}.zip", builder)
        self.assertIn(f'ARCHIVE_ROOT = "Barros_Pizza_Creator_AI_Designer_v{version}"', builder)
        self.assertIn('Copy-Item -Path (Join-Path $packageRoot "contracts\\*")', installer)


if __name__ == "__main__":
    unittest.main()
